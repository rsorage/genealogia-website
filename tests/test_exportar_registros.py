"""Verificações dos limites de publicação, usando apenas dados fictícios."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("exportar", Path(__file__).resolve().parents[1] / "scripts" / "exportar-registros.py")
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)
OPTIONAL_FIELDS = ("lote", "origem_tabela", "origem_linha", "origem_sha256", "incorporado_em",
                   "conferencia", "url_imagem_alternativa", "nota_publica")


class PublicSelection(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.source = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.names = [{"id": "L-0001", "nome": "Exemplo", "sobrenome": "Fictício", "ano": "1884",
                       "comune": "Local fictício", "serie": "Nati", "leitura": "certa",
                       "url_imagem": "https://antenati.cultura.gov.it/ark:/12657/exemplo/imagem",
                       "obs": "ANOTACAO_PRIVADA 1974 /Users/pesquisa/arquivo.md", "ficha": "INTERNO"}]
        self.pages = [{"ano": "1884", "comune": "Local fictício", "serie": "Nati", "cobertura": "procurada",
                       "url": "https://antenati.cultura.gov.it/ark:/12657/exemplo/imagem", "imagem": "7",
                       "conteudo": "Atos n.º 4 (Nome fictício; óbito 1974) e 5", "obs": "ANOTACAO_PRIVADA"}]

    def write(self):
        for name, rows, fields in [
            ("linhas-transcritas.csv", self.names, exporter.NAME_FIELDS + ("url_imagem", "obs", "ficha", "tipo_fonte", "idade") + OPTIONAL_FIELDS),
            ("mapa-imagens.csv", self.pages, exporter.PAGE_FIELDS + ("url", "conteudo", "obs")),
        ]:
            with (self.source / name).open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)

    def run_export(self, notes=None):
        self.write()
        return exporter.export(self.source, notes or {})

    def test_private_notes_and_later_annotations_do_not_escape(self):
        data, _ = self.run_export()
        self.assertNotIn("ANOTACAO_PRIVADA", str(data))
        self.assertNotIn("1974", str(data))
        self.assertNotIn("/Users/", str(data))
        self.assertNotIn("ficha", data["nomes"][0])
        self.assertEqual(data["paginas"][0]["descricao"], "Referência inicial: ato 4.")

    def test_modern_event_in_old_volume_is_excluded(self):
        self.names[0]["data_evento"] = "1974-01-01"
        data, report = self.run_export()
        self.assertEqual(data["nomes"], [])
        self.assertIn("posterior ao corte", report["excluidas"][0]["motivo"])

    def test_death_after_1925_needs_birth_by_1925(self):
        self.names[0].update(serie="Morti", tipo_fonte="morte", ano="1930", data_evento="1930-07-28",
                             idade="85", conjuge_nome="Cônjuge", conjuge_sobrenome="Fictício")
        data, _ = self.run_export()
        self.assertEqual(len(data["nomes"]), 1)
        self.assertEqual(data["nomes"][0]["conjuge_nome"], "Cônjuge")
        self.assertEqual(data["cortes"]["obitos"], 1955)

    def test_death_after_1925_without_age_is_excluded(self):
        self.names[0].update(serie="Morti", tipo_fonte="morte", ano="1930")
        data, report = self.run_export()
        self.assertEqual(data["nomes"], [])
        self.assertIn("nascimento comprovado", report["excluidas"][0]["motivo"])

    def test_death_of_person_born_after_1925_is_excluded(self):
        self.names[0].update(serie="Morti", tipo_fonte="morte", ano="1950", idade="20")
        data, report = self.run_export()
        self.assertEqual(data["nomes"], [])

    def test_explicit_birth_in_role_counts(self):
        self.names[0].update(serie="Morti", tipo_fonte="trascrizione", ano="1938", data_evento="1935-09-07",
                             papel="defunto (n. Laganadi 23/12/1856, segundo o ato)")
        data, _ = self.run_export()
        self.assertEqual(len(data["nomes"]), 1)

    def test_spouse_hidden_when_deceased_born_after_1900(self):
        self.names[0].update(serie="Morti", tipo_fonte="morte", ano="1940", idade="30",
                             conjuge_nome="Cônjuge", conjuge_sobrenome="Fictício")
        data, _ = self.run_export()
        self.assertEqual(data["nomes"][0]["conjuge_nome"], "")
        self.assertEqual(data["nomes"][0]["conjuge_sobrenome"], "")

    def test_cutoffs_by_record_type(self):
        for serie, tipo, year in (("Nati", "nascita", "1930"), ("Matrimoni", "matrimonio", "1930"), ("Morti", "morte", "1960")):
            self.names[0].update(serie=serie, tipo_fonte=tipo, ano=year, idade="80")
            data, _ = self.run_export()
            self.assertEqual(data["nomes"], [], (serie, year))

    def test_missing_url_is_not_published(self):
        self.names[0]["url_imagem"] = ""
        data, report = self.run_export()
        self.assertEqual(len(data["nomes"]), 0)
        self.assertEqual(len(report["excluidas"]), 1)

    def test_revisits_preserve_both_coverage_levels(self):
        self.pages.append(dict(self.pages[0], cobertura="lida inteira"))
        data, report = self.run_export()
        self.assertEqual(len(data["paginas"]), 1)
        self.assertEqual(data["paginas"][0]["coberturas"], ["lida inteira", "procurada"])
        self.assertEqual(data["paginas"][0]["anotacoes"], 2)
        self.assertEqual(report["consultas_repetidas_agrupadas"], 1)

    def test_coverage_not_upgraded_by_a_transcription(self):
        data, _ = self.run_export()
        self.assertEqual(data["paginas"][0]["coberturas"], ["procurada"])

    def test_page_links_stay_stable_after_reordering_and_new_description(self):
        before, _ = self.run_export()
        self.pages[0]["conteudo"] = "Descrição mais recente"
        self.pages[0]["imagem"] = "07"
        after, _ = self.run_export()
        self.assertEqual(before["paginas"][0]["id"], after["paginas"][0]["id"])

    def test_ambiguous_names_remain_ambiguous(self):
        self.names[0].update(nome="Nom[e?]", mae="M[ãe?]", leitura="provável")
        data, _ = self.run_export()
        self.assertEqual(data["nomes"][0]["mae"], "M[ãe?]")
        self.assertEqual(data["nomes"][0]["leitura"], "provável")

    def test_duplicate_name_id_stops_export(self):
        self.names.append(dict(self.names[0]))
        with self.assertRaisesRegex(ValueError, "repetido"):
            self.run_export()

    def test_orphan_public_note_stops_export(self):
        with self.assertRaisesRegex(ValueError, "ausentes"):
            self.run_export({"L-9999": "Nota pública"})

    def test_schema_change_stops_export(self):
        self.write()
        (self.source / "linhas-transcritas.csv").write_text("id,nome\nL-0001,Exemplo\n")
        with self.assertRaisesRegex(ValueError, "Colunas"):
            exporter.export(self.source, {})

    def test_sources_remain_unchanged(self):
        self.write()
        before = {p.name: p.read_bytes() for p in self.source.iterdir()}
        exporter.export(self.source, {})
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.source.iterdir()})

    def test_private_selection_omits_a_person_without_changing_source(self):
        self.write()
        data, report = exporter.export(self.source, {}, {"ocultar_ocorrencias": ["L-0001"]})
        self.assertEqual(data["nomes"], [])
        self.assertEqual(len(report["excluidas"]), 1)
        self.assertIn("Exemplo", (self.source / "linhas-transcritas.csv").read_text())

    def test_private_selection_omits_a_page(self):
        before, _ = self.run_export()
        data, _ = exporter.export(self.source, {}, {"ocultar_paginas": [before["paginas"][0]["id"]]})
        self.assertEqual(data["paginas"], [])

    def test_unknown_private_policy_cannot_be_silently_ignored(self):
        self.write()
        with self.assertRaisesRegex(ValueError, "Chave"):
            exporter.export(self.source, {}, {"ocultar_nomes": ["L-0001"]})

    def test_provenance_stays_private_but_review_is_visible(self):
        self.names[0].update(origem_tabela="/Users/private/ORIGEM.csv", origem_linha="55", origem_sha256="PRIVATE_SHA",
                             conferencia="imagem_sem_segunda_conferencia", nota_publica="Leitura provisória.")
        data, _ = self.run_export()
        self.assertNotIn("PRIVATE_SHA", str(data))
        self.assertNotIn("/Users/private", str(data))
        self.assertIn("sem segunda conferência", data["nomes"][0]["conferencia"])
        self.assertEqual(data["nomes"][0]["nota"], "Leitura provisória.")

    def test_unknown_review_state_stops_export(self):
        self.names[0]["conferencia"] = "confirmado_automaticamente"
        with self.assertRaisesRegex(ValueError, "conferência"):
            self.run_export()

    def test_bad_alternative_link_stops_export(self):
        self.names[0]["url_imagem_alternativa"] = "https://other.example/private"
        with self.assertRaisesRegex(ValueError, "alternativo"):
            self.run_export()

    def test_page_name_counts_include_primary_and_alternative_links(self):
        self.names[0]["url_imagem_alternativa"] = "https://www.familysearch.org/ark:/61903/3:1:EXEMPLO"
        self.pages.append(dict(self.pages[0], url=self.names[0]["url_imagem_alternativa"]))
        data, _ = self.run_export()
        self.assertEqual(len(data["nomes"][0]["paginas"]), 2)
        self.assertTrue(all(p["nomes_transcritos"] == 1 for p in data["paginas"]))

    def test_two_roles_remain_one_mention(self):
        self.names[0]["papel"] = "mãe, declarante"
        data, _ = self.run_export()
        self.assertEqual(len(data["nomes"]), 1)
        self.assertEqual(data["nomes"][0]["papeis"], ["Mãe", "Declarante"])


class Boundaries(unittest.TestCase):
    def test_act_group_joins_continuations_but_keeps_parts_and_series(self):
        row = {"url": "https://antenati.cultura.gov.it/ark:/12657/an_ua123/Canvas1", "num_atto": "1",
               "parte": "I", "comune": "Scilla", "serie": "Nati", "ano": "1884"}
        first = exporter.act_id(row)
        self.assertEqual(first, exporter.act_id(dict(row, url=row["url"].replace("Canvas1", "Canvas2"))))
        self.assertNotEqual(first, exporter.act_id(dict(row, parte="II")))
        self.assertNotEqual(first, exporter.act_id(dict(row, serie="Battesimi")))

    def test_uncertain_and_crossing_cutoff_years(self):
        for value in ("1908?", "", "1926", "1920–1930", "1890-1880"):
            self.assertIsNone(exporter.years(value), value)
        self.assertEqual(exporter.years("1881–1882"), (1881, 1882))
        self.assertEqual(exporter.years("1925"), (1925, 1925))

    def test_only_official_https_images(self):
        for value in (
            "javascript:alert(1)", "https://antenati.cultura.gov.it.evil.example/ark:/a",
            "https://login:secret@antenati.cultura.gov.it/ark:/a",
            "http://antenati.cultura.gov.it/ark:/a", "https://www.familysearch.org/tree/person/exemplo",
            "https://antenati.cultura.gov.it:8443/ark:/a",
        ):
            self.assertIsNone(exporter.public_url(value), value)

    def test_strip_auth_queries_but_keep_image_number_and_pdf_page(self):
        url, _ = exporter.public_url("https://www.familysearch.org/search/film/123?token=PRIVATE&i=17&cat=34")
        self.assertNotIn("PRIVATE", url)
        self.assertIn("i=17", url)
        url, _ = exporter.public_url("https://www.gazzettaufficiale.it/eli/gu/exemplo/pdf#page=16")
        self.assertTrue(url.endswith("#page=16"))

    def test_machine_transcription_is_not_exported_as_description(self):
        result = exporter.content_summary("ato 5 (nome da transcrição automática; não conferido)")
        self.assertNotIn("ato 5", result)
        self.assertNotIn("nome da transcrição", result)

    def test_earthquake_publication_is_not_marriage_banns(self):
        self.assertEqual(exporter.category("Elenco dei presunti morti, 1ª pubblicazione"), "Listas do terremoto")

    def test_changes_include_removals(self):
        before = {"nomes": [{"id": "L-0001", "nome": "Antes"}, {"id": "L-0002"}]}
        after = {"nomes": [{"id": "L-0001", "nome": "Depois"}, {"id": "L-0003"}], "paginas": []}
        changes = exporter.differences(before, after)["nomes"]
        self.assertEqual(changes, {"novas": ["L-0003"], "removidas": ["L-0002"], "alteradas": ["L-0001"]})


if __name__ == "__main__":
    unittest.main()
