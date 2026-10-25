#!/usr/bin/env python3
"""Incorpora apenas a amostra de Scilla/Nati 1884 ao índice privado.

Não consulta imagens, não resolve leituras, não publica e não altera o CSV de origem.
Uma repetição da importação preserva os identificadores e não duplica menções.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("04 Pesquisa/_leituras/scilla-1882-1886/amostra-nati-1884.csv")
BATCH = "scilla-amostra-nati-1884"
EXTRA_FIELDS = ("lote", "origem_tabela", "origem_linha", "origem_sha256", "incorporado_em",
                "conferencia", "url_imagem_alternativa", "nota_publica")
REQUIRED = {"imagem", "url_antenati", "ark_familysearch", "atto", "data_atto", "nato",
            "papel", "sobrenome", "nome", "idade", "oficio", "domicilio", "endereco_nascita", "obs"}


def norm(value: str) -> str:
    return unicodedata.normalize("NFC", " ".join((value or "").split())).casefold()


def part_and_number(value: str, part: str = "") -> tuple[str, str]:
    match = re.fullmatch(r"(?:(I|II)-)?(\d+)", value.strip())
    if not match:
        raise ValueError("Número de ato não reconhecido na amostra: " + value)
    return match[1] or part or "I", str(int(match[2]))


def role(row: dict) -> str:
    if row["papel"] == "dichiarante":
        return "mãe, declarante" if "a declarante é a mãe" in row["obs"] else "declarante"
    return {"madre": "mãe", "testimone": "testemunha"}[row["papel"]]


def reading(row: dict) -> str:
    nominal = row["nome"] + " " + row["sobrenome"]
    flagged = re.search(r"[?\[\]]", nominal) or re.search(
        r"sobrenome.*?\[\?\]|assina.*?\[\?\]|grafia ambígua|escrito.*? ou ", row["obs"], re.I)
    # O arquivo não fornece graus individuais. Não elevar ausência de ressalva a certeza.
    return "duvidosa" if flagged else "provável"


def public_note(row: dict) -> str:
    notes = []
    if reading(row) == "duvidosa":
        notes.append("A amostra registra dúvida na leitura do nome ou sobrenome; confira a imagem.")
    if "grafia ambígua «Siclari»/«Sidari»" in row["obs"]:
        notes.append("As leituras Siclari e Sidari permanecem em aberto.")
    if "o ato continua na imagem 115, não lida" in row["obs"]:
        notes.append("A transcrição cobre o trecho da imagem 114. O ato continua na imagem 115, não lida nesta amostra.")
    return " ".join(notes)


def read_table(path: Path) -> tuple[list[str], list[dict], bytes]:
    raw = path.read_bytes()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    rows = list(reader)
    if not reader.fieldnames or any(None in row for row in rows):
        raise ValueError("Estrutura CSV irregular: " + path.name)
    return reader.fieldnames, rows, raw


def same_occurrence(candidate: dict, current: dict) -> bool:
    if any(norm(candidate[k]) != norm(current.get(k, "")) for k in ("nome", "sobrenome", "comune", "serie", "ano")):
        return False
    try:
        if part_and_number(candidate["num_atto"], candidate["parte"]) != part_and_number(current.get("num_atto", ""), current.get("parte", "")):
            return False
    except ValueError:
        return False
    roles = {"dichiarante": "declarante", "testimone": "testemunha", "madre": "mãe"}
    if norm(candidate["papel"]) != roles.get(norm(current.get("papel", "")), norm(current.get("papel", ""))):
        return False
    candidate_urls = {candidate["url_imagem"], candidate["url_imagem_alternativa"]} - {""}
    current_urls = {current.get("url_imagem", ""), current.get("url_imagem_alternativa", "")} - {""}
    return bool(candidate_urls & current_urls)


def prepare(sample: list[dict], central: list[dict], pages: list[dict], source_sha: str, imported_on: str) -> tuple[list[dict], dict]:
    if any(row.get("lote") == BATCH and row.get("origem_sha256") != source_sha for row in central):
        raise ValueError("A amostra foi modificada após a incorporação; revisar antes de reimportar.")
    result = [dict(row) for row in central]
    numbers = []
    for row in central:
        match = re.fullmatch(r"L-(\d+)", row["id"])
        if not match:
            raise ValueError("Identificador irregular no índice central.")
        numbers.append(int(match[1]))
    if len(numbers) != len(set(numbers)):
        raise ValueError("Identificador repetido no índice central.")
    next_id = max(numbers, default=0) + 1
    added, existing, provenance, keys = [], [], [], set()
    for line, row in enumerate(sample, 2):
        if row["papel"] not in {"dichiarante", "madre", "testimone"}:
            raise ValueError(f"Papel não reconhecido na linha {line}.")
        if not row["nome"].strip() or not row["sobrenome"].strip():
            raise ValueError(f"Nome incompleto na linha {line}; manter pendente.")
        if not re.fullmatch(r"1884-\d{2}-\d{2}", row["data_atto"]):
            raise ValueError(f"Data fora da amostra na linha {line}.")
        date.fromisoformat(row["data_atto"])
        if not re.fullmatch(r"https://antenati\.cultura\.gov\.it/ark:/12657/an_ua16601247/[A-Za-z0-9]+", row["url_antenati"]):
            raise ValueError(f"Imagem fora do volume esperado na linha {line}.")
        if not re.fullmatch(r"https://www\.familysearch\.org/ark:/61903/3:1:[A-Za-z0-9-]+", row["ark_familysearch"]):
            raise ValueError(f"Link alternativo não reconhecido na linha {line}.")
        part, number = part_and_number(row["atto"])
        matching_pages = [p for p in pages if p.get("url") == row["url_antenati"]
                          and p.get("comune") == "Scilla" and p.get("serie") == "Nati"
                          and p.get("ano") == "1884" and str(p.get("imagem", "")).lstrip("0") == row["imagem"].lstrip("0")]
        if not matching_pages or not any(p.get("cobertura") == "lida inteira" for p in matching_pages):
            raise ValueError(f"Imagem da linha {line} sem leitura registrada no mapa central.")
        read_dates = [p["lido_em"] for p in matching_pages if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.get("lido_em", ""))]
        if not read_dates:
            raise ValueError(f"Data da leitura ausente na linha {line}.")
        candidate = dict.fromkeys(central[0].keys() if central else (), "")
        candidate.update(repositorio="antenati", url_imagem=row["url_antenati"], imagem=row["imagem"],
                         comune="Scilla", serie="Nati", ano="1884", parte=part, tipo_fonte="nascita",
                         num_atto=number, data_evento=row["data_atto"], sobrenome=row["sobrenome"], nome=row["nome"],
                         pai="", mae="", conjuge_sobrenome="", conjuge_nome="", idade=row["idade"],
                         residencia=row["domicilio"], papel=role(row), leitura=reading(row), ficha="",
                         lido_em=min(read_dates), obs=row["obs"], lote=BATCH, origem_tabela=SOURCE.as_posix(),
                         origem_linha=str(line), origem_sha256=source_sha, incorporado_em=imported_on,
                         conferencia="imagem_sem_segunda_conferencia", url_imagem_alternativa=row["ark_familysearch"],
                         nota_publica=public_note(row))
        # Não inferir pai/cônjuge do papel de declarante, nem o sobrenome da criança.
        key = tuple(candidate[k] for k in ("url_imagem", "parte", "num_atto", "papel", "nome", "sobrenome"))
        if key in keys:
            raise ValueError(f"Menção repetida dentro da amostra, linha {line}.")
        keys.add(key)
        matches = [current for current in result if same_occurrence(candidate, current)]
        if len(matches) > 1:
            raise ValueError(f"Mais de uma correspondência central para a linha {line}.")
        if matches:
            current = matches[0]
            if current.get("lote") == BATCH and current.get("origem_sha256") != source_sha:
                raise ValueError("A amostra foi modificada após a incorporação; revisar antes de reimportar.")
            existing.append(current["id"])
            identifier = current["id"]
        else:
            identifier = f"L-{next_id:04d}"
            next_id += 1
            candidate["id"] = identifier
            result.append(candidate)
            added.append(identifier)
        provenance.append({"linha_origem": line, "id": identifier, "imagem": row["imagem"],
                           "parte": part, "ato": number, "papel_origem": row["papel"],
                           "leitura_incorporada": candidate["leitura"]})
    report = {"lote": BATCH, "origem": SOURCE.as_posix(), "sha256_origem": source_sha,
              "incorporado_em": imported_on, "menções_origem": len(sample), "novas": added, "já_presentes": existing,
              "atos": len({(r["parte"], r["ato"]) for r in provenance}),
              "imagens": len({r["imagem"] for r in provenance}),
              "papeis_origem": dict(Counter(row["papel"] for row in sample)),
              "graus_propostos": dict(Counter(reading(row) for row in sample)), "rastreio": provenance}
    return result, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acervo", type=Path, default=ROOT.parent / "family-research")
    parser.add_argument("--verificar", action="store_true", help="não grava; retorna 1 se houver menções por incorporar")
    args = parser.parse_args()
    central_path = args.acervo / "01 Indice/registros-vistos/linhas-transcritas.csv"
    page_path = central_path.with_name("mapa-imagens.csv")
    sample_path = args.acervo / SOURCE
    source_fields, sample, source_raw = read_table(sample_path)
    if not REQUIRED.issubset(source_fields):
        raise ValueError("Colunas obrigatórias ausentes na amostra.")
    fields, central, central_raw = read_table(central_path)
    _, pages, _ = read_table(page_path)
    source_sha = hashlib.sha256(source_raw).hexdigest()
    imported_on = datetime.now(ZoneInfo("Europe/Berlin")).date().isoformat()
    result, report = prepare(sample, central, pages, source_sha, imported_on)
    print(f"Amostra: {len(sample)} menções, {report['atos']} atos, {report['imagens']} imagens.")
    print(f"Novas: {len(report['novas'])}; já presentes: {len(report['já_presentes'])}.")
    print("Graus de leitura: " + json.dumps(report["graus_propostos"], ensure_ascii=False) + ".")
    if args.verificar:
        return int(bool(report["novas"]))
    if not report["novas"]:
        print("Lote já incorporado; nenhum arquivo alterado.")
        return 0
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields + [k for k in EXTRA_FIELDS if k not in fields], lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(result)
    # Não sobrescrever uma inclusão feita por outra sessão enquanto consolidávamos.
    if central_path.read_bytes() != central_raw or sample_path.read_bytes() != source_raw:
        raise ValueError("O índice ou a amostra mudou durante a operação. Executar novamente para preservar as novas entradas.")
    batch_dir = central_path.parent / "lotes" / BATCH
    batch_dir.mkdir(parents=True, exist_ok=True)
    backup = batch_dir / "linhas-antes.csv.txt"
    if backup.exists():
        raise ValueError("Já existe um histórico deste lote; revisar antes de acrescentar novas linhas.")
    backup.write_bytes(central_raw)
    (batch_dir / "consolidacao.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    temporary = central_path.with_suffix(".csv.tmp")
    temporary.write_bytes(output.getvalue().encode("utf-8"))
    if central_path.read_bytes() != central_raw:
        temporary.unlink()
        raise ValueError("O índice mudou antes da gravação. O histórico privado foi preservado; revisar antes de repetir.")
    temporary.replace(central_path)
    print("Índice privado atualizado; origem preservada e rastreio salvo no lote. Nenhuma publicação realizada.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, csv.Error) as error:
        print(f"Consolidação interrompida: {error}", file=sys.stderr)
        sys.exit(2)
