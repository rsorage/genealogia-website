"""Regressões de proveniência, repetição e papéis na importação da amostra."""
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("consolidar", Path(__file__).resolve().parents[1] / "scripts" / "consolidar-scilla.py")
consolidator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(consolidator)


class SampleImport(unittest.TestCase):
    def setUp(self):
        self.sample = [{
            "imagem": "4", "url_antenati": "https://antenati.cultura.gov.it/ark:/12657/an_ua16601247/Exemplo",
            "ark_familysearch": "https://www.familysearch.org/ark:/61903/3:1:EXEMPLO",
            "atto": "7", "data_atto": "1884-01-03", "nato": "Criança sem sobrenome transcrito",
            "papel": "dichiarante", "sobrenome": "Fictício", "nome": "Exemplo", "idade": "30",
            "oficio": "ofício fictício", "domicilio": "Scilla", "endereco_nascita": "ENDERECO_DA_CRIANCA",
            "obs": "",
        }]
        self.pages = [{"url": self.sample[0]["url_antenati"], "comune": "Scilla", "serie": "Nati",
                       "ano": "1884", "imagem": "4", "cobertura": "lida inteira", "lido_em": "2026-10-24"}]

    def prepare(self, central=None, sha="SOURCE_SHA"):
        return consolidator.prepare(self.sample, central or [], self.pages, sha, "2026-10-25")

    def test_declarante_is_not_automatically_father(self):
        rows, _ = self.prepare()
        self.assertEqual(rows[0]["papel"], "declarante")
        for field in ["pai", "mae", "conjuge_nome", "conjuge_sobrenome"]:
            self.assertEqual(rows[0][field], "")
        self.assertNotIn("ENDERECO_DA_CRIANCA", str(rows))
        self.assertEqual(len(rows), 1)  # Não inventar uma nova ocorrência para a criança.

    def test_no_individual_grade_does_not_become_certain(self):
        rows, _ = self.prepare()
        self.assertEqual(rows[0]["leitura"], "provável")
        self.assertEqual(rows[0]["lido_em"], "2026-10-24")
        self.assertEqual(rows[0]["incorporado_em"], "2026-10-25")

    def test_existing_uncertainty_is_preserved(self):
        self.sample[0]["sobrenome"] = "Nom[e?]"
        rows, _ = self.prepare()
        self.assertEqual(rows[0]["sobrenome"], "Nom[e?]")
        self.assertEqual(rows[0]["leitura"], "duvidosa")

    def test_uncertainty_in_observation_is_not_discarded(self):
        self.sample[0]["obs"] = "sobrenome Exemplo[?] (OCR: INCERTO_OCR)"
        rows, _ = self.prepare()
        self.assertEqual(rows[0]["leitura"], "duvidosa")
        self.assertNotIn("INCERTO_OCR", rows[0]["nota_publica"])

    def test_idempotent_and_old_ids_preserved(self):
        before, _ = self.prepare()
        after, report = self.prepare(before)
        self.assertEqual(before, after)
        self.assertEqual(report["novas"], [])
        self.assertEqual(report["já_presentes"], ["L-0001"])

    def test_next_identifier_does_not_overwrite_another_batch(self):
        before, _ = self.prepare()
        old = dict(before[0], id="L-0250", nome="Outro", lote="outro-lote")
        after, report = self.prepare([old])
        self.assertEqual(after[0], old)
        self.assertEqual(report["novas"], ["L-0251"])

    def test_same_person_in_different_acts_remains_two_mentions(self):
        self.sample.append(dict(self.sample[0], atto="8"))
        rows, report = self.prepare()
        self.assertEqual(len(rows), 2)
        self.assertEqual(report["atos"], 2)

    def test_duplicate_source_row_stops_import(self):
        self.sample.append(dict(self.sample[0]))
        with self.assertRaisesRegex(ValueError, "repetida"):
            self.prepare()

    def test_part_two_is_explicit(self):
        self.sample[0]["atto"] = "II-1"
        rows, _ = self.prepare()
        self.assertEqual((rows[0]["parte"], rows[0]["num_atto"]), ("II", "1"))

    def test_mother_declaring_does_not_become_two_rows(self):
        self.sample[0]["obs"] = "a declarante é a mãe, solteira"
        rows, _ = self.prepare()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["papel"], "mãe, declarante")

    def test_missing_image_reading_stops_import(self):
        self.pages[0]["cobertura"] = "cabeçalho"
        with self.assertRaisesRegex(ValueError, "sem leitura"):
            self.prepare()

    def test_changed_source_requires_review(self):
        before, _ = self.prepare()
        with self.assertRaisesRegex(ValueError, "modificada"):
            self.prepare(before, sha="CHANGED")

    def test_partial_act_warning_survives(self):
        self.sample[0]["obs"] = "o ato continua na imagem 115, não lida"
        rows, _ = self.prepare()
        self.assertIn("115, não lida", rows[0]["nota_publica"])

    def test_corresponding_familysearch_copy_does_not_duplicate(self):
        before, _ = self.prepare()
        before[0].update(url_imagem=self.sample[0]["ark_familysearch"], url_imagem_alternativa="", lote="")
        after, report = self.prepare(before)
        self.assertEqual(after, before)
        self.assertEqual(report["novas"], [])


if __name__ == "__main__":
    unittest.main()
