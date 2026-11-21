import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag import NO_ANSWER, Rag, ServiceError, Settings, read_documents, split_document


class TestIntegracao(unittest.TestCase):
    """Executa contra Qdrant e Ollama reais, após a preparação dos modelos."""

    @classmethod
    def setUpClass(cls):
        cls.rag = Rag()
        cls.first_index = cls.rag.index()

    def test_01_indexacao_repetida_nao_duplica_vetores(self):
        second = self.rag.index()
        self.assertEqual(second["collection"], self.first_index["collection"])
        self.assertEqual(second["chunks"], self.first_index["chunks"])
        self.assertGreater(second["dimension"], 100)
        self.assertEqual(second["documents"], 12)

    def test_02_recuperacao_por_significado(self):
        cases = [
            ("Quero algo para carregar meu computador nas costas.", "08_mochila.md"),
            ("Preciso iluminar minha mesa de estudo.", "12_luminaria.md"),
            ("Tem recipiente térmico de meio litro?", "09_garrafa.md"),
            ("Quero escrever com uma ponta de sete décimos de milímetro.", "10_caneta.md"),
            ("Quanto custa o caderno e quantas folhas ele tem?", "07_caderno.md"),
            ("Vocês levam compras até minha casa em Teresina?", "03_entrega.md"),
        ]
        for question, expected in cases:
            with self.subTest(question=question):
                result = self.rag.retrieve(question)
                self.assertIn(expected, [item["file"] for item in result["matches"]])

    def test_03_pergunta_fora_do_dominio_nao_aciona_geracao(self):
        result = self.rag.answer("Qual a composição química da atmosfera de Júpiter?")
        self.assertFalse(result["generated"])
        self.assertEqual(result["answer"], NO_ANSWER)
        self.assertEqual(result["sources"], [])

    def test_04_geracao_utiliza_ficha_recuperada(self):
        result = self.rag.answer("Qual a capacidade da Garrafa Essencial e o preço no catálogo inicial?")
        self.assertTrue(result["generated"])
        self.assertIn("500", result["answer"])
        self.assertRegex(result["answer"], r"59[,.]90")
        self.assertTrue(result["sources"])
        used = [item["file"] for item in result["matches"] if item["label"] in result["sources"]]
        self.assertIn("09_garrafa.md", used)

    def test_05_caracteristica_nao_documentada(self):
        result = self.rag.answer("Quantas horas dura a bateria do Fone Studio?")
        self.assertTrue(any(item["file"] == "11_fone.md" for item in result["matches"]))
        self.assertRegex(result["answer"].casefold(), r"não|nao|insuficiente|informad|especificad")
        self.assertNotRegex(result["answer"], r"\b\d+\s*(horas|h)\b")

    def test_06_mudanca_documental_bloqueia_indice_antigo(self):
        with tempfile.TemporaryDirectory(prefix="essencia-rag-test-") as temp:
            folder = Path(temp)
            for doc in self.rag.settings.documents_dir.glob("*.md"):
                shutil.copyfile(doc, folder / doc.name)
            (folder / "novo.md").write_text("# Novo guia\nConteúdo novo para o teste.", encoding="utf-8")
            altered = Rag(replace(self.rag.settings, documents_dir=folder))
            with self.assertRaisesRegex(ServiceError, "mudaram"):
                altered.manifest()

    def test_07_limites_da_pergunta(self):
        for question in [" ", "a" * 601]:
            with self.assertRaises(ValueError):
                self.rag.retrieve(question)

    def test_08_divisao_preserva_cobertura_do_documento(self):
        for doc in read_documents(self.rag.settings.documents_dir):
            chunks = split_document(doc)
            self.assertTrue(chunks)
            self.assertEqual(chunks[0]["text"], doc["text"][:len(chunks[0]["text"])])
            self.assertTrue(doc["text"].endswith(chunks[-1]["text"]))
            self.assertTrue(all(len(chunk["text"]) <= 850 for chunk in chunks))


if __name__ == "__main__":
    unittest.main(verbosity=2)
