"""Páginas de transcrições legíveis sem JavaScript, usando só dados já públicos."""
from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date
from pathlib import Path

SITE = "https://genealogia.rsorage.com"
BASE = "registros-vistos/catalogo/"
MANIFEST = "scripts/registros-vistos/gerados.json"
MARKER = "<!-- Gerado por exportar-registros.py: catalogo-estatico-v1 -->"
SITEMAP_START = "  <!-- Inicio das listagens geradas de Registros vistos -->"
SITEMAP_END = "  <!-- Fim das listagens geradas de Registros vistos -->"


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def slug(value: str) -> str:
    plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    plain = re.sub(r"[^a-z0-9]+", "-", plain).strip("-") or "sem-identificacao"
    if len(plain) > 80:
        plain = plain[:70].rstrip("-") + "-" + hashlib.sha256(value.encode()).hexdigest()[:8]
    return plain


def make_groups(data: dict) -> list[dict]:
    grouped = defaultdict(list)
    for row in data["nomes"]:
        grouped[(row["comune"], row["serie"], row["ano"])].append(row)
    routes = {}
    groups = []
    for (place, series, year), rows in sorted(grouped.items()):
        path = BASE + "/".join(map(slug, (place, series, year))) + "/"
        if path in routes:
            raise ValueError("Dois recortes produzem o mesmo endereço; revisar os rótulos antes de gerar: " + path)
        routes[path] = (place, series, year)
        for row in rows:
            row["url_catalogo"] = "/" + path
        groups.append({"comune": place, "serie": series, "ano": year, "rows": rows, "path": path})
    return groups


EXTRA_CSS = """
.breadcrumbs{font:13px/1.7 Arial,Helvetica,sans-serif;margin:26px 0 0;gap:10px;overflow-wrap:anywhere}
.breadcrumbs a{color:var(--accent);text-decoration:underline}.breadcrumbs span{color:var(--muted)}
.static-hero{padding:35px 0 30px;max-width:880px}.static-hero h1{font-size:clamp(36px,5vw,62px);overflow-wrap:anywhere}
.static-hero .intro{font-size:20px}.static-hero .series{display:block;font-size:.62em;line-height:1.4;letter-spacing:-.025em;margin-top:15px;color:var(--accent)}
.browse{margin:36px 0 48px;border-top:1px solid var(--line);padding-top:28px}.browse h2{font:400 32px/1.25 Georgia,serif;letter-spacing:-.025em;margin:0 0 15px}.browse>p{max-width:780px;margin:0 0 22px;font:15px/1.8 Arial,sans-serif}
.browse-groups{display:grid;grid-template-columns:1fr 1fr;gap:28px 48px}.browse-place{min-width:0}.browse-place h3{font:400 25px/1.3 Georgia,serif;margin:0 0 12px}.browse-place ul{padding:0;margin:0;list-style:none;border-top:1px solid var(--line)}
.browse-place li{padding:10px 0;border-bottom:1px solid var(--line);font:14px/1.7 Arial,sans-serif;overflow-wrap:anywhere}.browse-place small{display:block;color:var(--muted);font-size:12px}.browse-link{font:14px/1.7 Arial,sans-serif;margin:18px 0 0}
.static-toc{font:14px/1.8 Arial,sans-serif;margin:24px 0 35px}.static-toc summary{color:var(--accent)}.static-toc ul{padding-left:22px;columns:3;column-gap:35px}.static-toc li{break-inside:avoid;padding:3px 0}
.static-act{margin:40px 0 0;scroll-margin-top:24px}.static-act>h2{font:400 29px/1.3 Georgia,serif;letter-spacing:-.025em;border-bottom:1px solid var(--line);padding-bottom:13px;margin:0}.static-act>p{font:13px/1.8 Arial,sans-serif;color:var(--muted);margin:10px 0}
.static-person{padding:24px 0;border-bottom:1px solid var(--line);scroll-margin-top:24px;overflow-wrap:anywhere}.static-person:target{background:var(--white)}.static-person>h3{font:400 26px/1.3 Georgia,serif;margin:0 0 10px}.static-person .person-meta{display:flex;gap:12px;flex-wrap:wrap;align-items:baseline;font:14px/1.7 Arial,sans-serif;color:var(--muted);margin:0 0 18px}
.static-person dl{display:grid;grid-template-columns:120px minmax(0,1fr);gap:8px 24px;margin:0 0 18px;font:14px/1.8 Arial,sans-serif}.static-person dt{color:var(--muted)}.static-person dd{margin:0}.static-person .record-note{font:14px/1.8 Arial,sans-serif}.static-person .record-actions{margin-top:16px}
.static-notes{font:14px/1.8 Arial,sans-serif;margin:36px 0 45px;max-width:820px;border-top:1px solid var(--line);padding-top:22px}.static-notes p{margin:0 0 14px}
@media(max-width:680px){.browse-groups{grid-template-columns:1fr;gap:26px}.browse h2{font-size:28px}.static-hero h1{font-size:39px}.static-hero .intro{font-size:18px}.static-person dl{grid-template-columns:1fr;gap:1px}.static-person dd{margin-bottom:10px}.static-toc ul{columns:2}.static-person>h3{font-size:24px}.static-act>h2{font-size:26px}}
@media(max-width:370px){.static-toc ul{columns:1}}
"""


def browse_html(groups: list[dict]) -> str:
    places = defaultdict(list)
    for group in groups:
        places[group["comune"]].append(group)
    sections = []
    for place, entries in places.items():
        links = []
        for group in entries:
            count = len(group["rows"])
            links.append(f'<li><a href="/{esc(group["path"])}">{esc(group["serie"])} · {esc(group["ano"])}</a>'
                         f'<small>{count} {"ocorrência transcrita" if count == 1 else "ocorrências transcritas"}</small></li>')
        sections.append(f'<section class="browse-place"><h3>{esc(place)}</h3><ul>{"".join(links)}</ul></section>')
    return '<div class="browse-groups">' + "".join(sections) + '</div>'


def frame(template: str, title: str, description: str, path: str, content: str) -> str:
    style = re.search(r'<style>(.*?)</style>', template, re.S)
    header = re.search(r'<header class="masthead">.*?</header>', template, re.S)
    icon = re.search(r'<link rel="icon"[^>]+>', template)
    if not all((style, header, icon)):
        raise ValueError("Cabeçalho, ícone ou estilos não encontrados no modelo principal.")
    url = SITE + "/" + path
    breadcrumbs = [{"@type": "ListItem", "position": 1, "name": "Registros vistos", "item": SITE + "/registros-vistos/"}]
    if path != BASE:
        breadcrumbs.append({"@type": "ListItem", "position": 2, "name": "Transcrições por localidade e ano", "item": SITE + "/" + BASE})
    breadcrumbs.append({"@type": "ListItem", "position": len(breadcrumbs) + 1, "name": title, "item": url})
    structured = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": breadcrumbs},
                            ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | Cardillo &amp; Sorage</title><meta name="description" content="{esc(description)}">
<meta name="author" content="Ramon Sorage"><meta name="theme-color" content="#f5f2eb">
<link rel="canonical" href="{esc(url)}"><meta property="og:type" content="website"><meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Cardillo &amp; Sorage"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="{SITE}/assets/og/portal.jpg"><meta property="og:image:alt" content="Cardillo e Sorage · da Itália a Minas Gerais">
<meta name="twitter:card" content="summary_large_image">{icon[0]}
<script type="application/ld+json">{structured}</script><style>{style[1].replace('__ESTILOS_CATALOGO__', '')}{EXTRA_CSS}</style></head>
<body>{MARKER}<a class="skip" href="#conteudo">Ir para o conteúdo</a><div class="wrap">
{header[0].replace('aria-current="page"', 'aria-current="location"')}
<main id="conteudo">{content}</main><footer><div><p>Cardillo &amp; Sorage · Um registro para a família e para o futuro.</p>
<p>Texto e pesquisa de Ramon Sorage · <a href="mailto:rsorage@gmail.com">rsorage@gmail.com</a></p></div>
<p><a href="/registros-vistos/">Voltar à busca</a></p></footer></div></body></html>
'''


def role_label(row: dict) -> str:
    raw = row["papel"]
    if len(row.get("papeis", [])) == 1 and row["papeis"][0] != "Pessoa registrada":
        return row["papeis"][0]
    if raw == "mãe, declarante":
        return "Mãe e declarante"
    return raw[:1].upper() + raw[1:]


def reference(row: dict) -> str:
    return " · ".join(v for v in (row["serie"], row["ano"], "Parte " + row["parte"] if row["parte"] else "",
                                      "Ato / n.º " + row["num_atto"] if row["num_atto"] else "",
                                      "Imagem " + row["imagem"] if row["imagem"] else "") if v)


def person_html(row: dict) -> str:
    terms = []
    values = [("Papel no ato", row["papel"]), ("Pai", row["pai"]), ("Mãe", row["mae"]),
              ("Cônjuge", " ".join(v for v in (row["conjuge_nome"], row["conjuge_sobrenome"]) if v)),
              ("Data indicada", re.sub(r"^(\d{4})-(\d{2})-(\d{2})$", r"\3/\2/\1", row["data_evento"])),
              ("Referência", reference(row)),
              ("Ressalva de leitura", row["leitura"].partition(" (")[2].removesuffix(")")),
              ("Conferência", row.get("conferencia", "")), ("Portal de origem", row["portal"])]
    for label, value in values:
        if value:
            terms.append(f'<dt>{esc(label)}</dt><dd>{esc(value)}</dd>')
    grade_class = "badge tag " + {"certa": "doc", "provável": "prov", "duvidosa": "hip"}[row["leitura"].split(" (")[0]]
    note = f'<p class="record-note">{esc(row["nota"])}</p>' if row["nota"] else ""
    links = [f'<a href="{esc(row["url"])}" target="_blank" rel="noopener noreferrer">Conferir no portal de origem&nbsp;↗</a>']
    if row.get("url_alternativa"):
        links.append(f'<a href="{esc(row["url_alternativa"])}" target="_blank" rel="noopener noreferrer">Ver também no {esc(row["portal_alternativo"])}&nbsp;↗</a>')
    links.append(f'<a href="{esc(row["url_catalogo"])}#{esc(row["id"])}">Link desta ocorrência</a>')
    return (f'<article class="static-person" id="{esc(row["id"])}"><h3>{esc(row["nome"])} {esc(row["sobrenome"])}</h3>'
            f'<p class="person-meta"><span>{esc(role_label(row))}</span><span class="{grade_class}">Leitura {esc(row["leitura"].split(" (")[0])}</span></p>'
            f'<dl>{"".join(terms)}</dl>{note}<div class="record-actions">{"".join(links)}</div></article>')


def render_static(template: str, groups: list[dict]) -> dict[str, str]:
    result = {}
    index_body = ('<nav class="breadcrumbs" aria-label="Caminho"><a href="/registros-vistos/">Registros vistos</a><span aria-hidden="true">/</span><span aria-current="page">Listagens</span></nav>'
                  '<section class="hero static-hero"><p class="eyebrow">Registros vistos · consulta por fonte</p>'
                  '<h1>Transcrições por <em>localidade e ano.</em></h1><p class="intro">Nomes que anotamos nos livros e documentos consultados, com referências para conferir as imagens originais.</p></section>'
                  '<aside class="notice"><strong>Transcrições parciais.</strong> Os recortes abaixo não representam cobertura completa dos anos ou livros. Uma ausência nesta lista não prova ausência no documento.</aside>'
                  '<section class="browse" aria-label="Listagens de transcrições">' + browse_html(groups) + '</section>')
    result[BASE + "index.html"] = frame(template, "Transcrições parciais por localidade e ano", "Explore nomes transcritos de registros históricos por localidade, série e ano, com graus de leitura e links para os documentos de origem.", BASE, index_body)
    for group in groups:
        place, series, year = group["comune"], group["serie"], group["ano"]
        acts = defaultdict(list)
        for row in group["rows"]:
            acts[row.get("ato_id") or row["id"]].append(row)

        def order(key):
            row = acts[key][0]
            raw = row["num_atto"]
            return (row["parte"], int(raw) if raw.isdigit() else 10**9, raw, key)

        sections, toc = [], []
        for key in sorted(acts, key=order):
            rows = acts[key]
            first = rows[0]
            label = ("Ato / n.º " + first["num_atto"]) if first["num_atto"] else "Referência transcrita"
            if first["parte"]:
                label += " · Parte " + first["parte"]
            section_id = key if key.startswith("A-") else "ref-" + key
            toc.append(f'<li><a href="#{esc(section_id)}">{esc(label)}</a></li>')
            sections.append(f'<section class="static-act" id="{esc(section_id)}"><h2>{esc(label)}</h2>'
                            '<p>Participantes transcritos; a lista pode não incluir todos os nomes do documento.</p>'
                            + "".join(person_html(row) for row in rows) + '</section>')
        title = f"{place} — {series}, {year}: transcrições parciais"
        description = f"Nomes e participantes transcritos parcialmente em {series} de {place}, {year}. Referências, graus de leitura e links para conferir os originais."
        body = (f'<nav class="breadcrumbs" aria-label="Caminho"><a href="/registros-vistos/">Registros vistos</a><span aria-hidden="true">/</span><a href="/{BASE}">Listagens</a><span aria-hidden="true">/</span><span aria-current="page">{esc(place)} · {esc(year)}</span></nav>'
                f'<section class="hero static-hero"><p class="eyebrow">Registros vistos · transcrições parciais</p><h1>{esc(place)}<span class="series">{esc(series)} · {esc(year)}</span></h1>'
                f'<p class="intro">{len(group["rows"])} {"ocorrência transcrita" if len(group["rows"]) == 1 else "ocorrências transcritas"} deste recorte, com os papéis de cada participante e as referências dos documentos.</p></section>'
                '<aside class="notice"><strong>Uma pista para continuar sua pesquisa.</strong> Esta transcrição é parcial. Não encontrar um nome aqui não significa que esteja ausente dos documentos. Os graus de leitura não confirmam identidade ou parentesco. <a href="/registros-vistos/#sobre">Entenda os limites da lista&nbsp;→</a></aside>'
                f'<details class="static-toc"><summary>Ir para uma referência</summary><ul>{"".join(toc)}</ul></details>'
                + "".join(sections) + '<aside class="static-notes"><p>As imagens permanecem nos portais de origem, que podem exigir cadastro ou restringir o acesso. Este catálogo é independente desses serviços.</p>'
                '<p>Os nomes são preservados como transcritos, inclusive seus sinais de dúvida. As transcrições podem conter erros; confira a imagem original antes de usar uma informação. A presença de pessoas no mesmo documento não estabelece parentesco entre elas.</p>'
                '<p>Viu um erro? Escreva para <a href="mailto:rsorage@gmail.com">rsorage@gmail.com</a>, indicando o link da ocorrência e a referência.</p>'
                f'<p><a href="/{BASE}">Explorar outras localidades e anos&nbsp;→</a></p></aside>')
        result[group["path"] + "index.html"] = frame(template, title, description, group["path"], body)
    return result


def valid_owned_path(value: str) -> bool:
    return (value == "registros-vistos/index.html" or value.startswith(BASE)) and value.endswith("/index.html") and not any(p in {".", ".."} for p in value.split("/")) and not value.startswith("/")


def load_manifest(root: Path) -> dict:
    path = root / MANIFEST
    if not path.exists():
        return {"version": 1, "files": {}}
    manifest = json.loads(path.read_text())
    if manifest.get("version") != 1 or not isinstance(manifest.get("files"), dict):
        raise ValueError("Manifesto de páginas geradas inválido.")
    for path, entry in manifest["files"].items():
        if not valid_owned_path(path) or not re.fullmatch(r"[a-f0-9]{64}", entry.get("sha256", "")):
            raise ValueError("Caminho ou assinatura inválida no manifesto de páginas geradas.")
        date.fromisoformat(entry["lastmod"])
    return manifest


def inventory(documents: dict[str, str], previous: dict, today: str) -> dict:
    date.fromisoformat(today)
    files = {}
    for path, document in documents.items():
        if not valid_owned_path(path):
            raise ValueError("Caminho inesperado de página gerada.")
        digest = hashlib.sha256(document.encode()).hexdigest()
        old = previous.get("files", {}).get(path, {})
        files[path] = {"sha256": digest, "lastmod": old["lastmod"] if old.get("sha256") == digest else today}
    return {"version": 1, "files": files}


def sitemap_document(original: str, manifest: dict) -> str:
    ET.fromstring(original)
    files = manifest["files"]
    catalog = "registros-vistos/index.html"
    if catalog not in files:
        raise ValueError("Página principal ausente do inventário.")
    pattern = r'(<url>\s*<loc>https://genealogia\.rsorage\.com/registros-vistos/</loc>\s*<lastmod>)[^<]*(</lastmod>\s*</url>)'
    result, count = re.subn(pattern, lambda m: m[1] + files[catalog]["lastmod"] + m[2], original)
    if count != 1:
        raise ValueError("Entrada principal do catálogo ausente ou repetida no sitemap.")
    entries = []
    for path, entry in sorted(files.items()):
        if path.startswith(BASE):
            entries.append(f'  <url><loc>{SITE}/{path.removesuffix("index.html")}</loc><lastmod>{entry["lastmod"]}</lastmod></url>')
    section = SITEMAP_START + "\n" + "\n".join(entries) + "\n" + SITEMAP_END
    if SITEMAP_START in result or SITEMAP_END in result:
        if result.count(SITEMAP_START) != 1 or result.count(SITEMAP_END) != 1:
            raise ValueError("Marcadores de listagens irregulares no sitemap.")
        result = re.sub(re.escape(SITEMAP_START) + r'.*?' + re.escape(SITEMAP_END), lambda _: section, result, flags=re.S)
    else:
        result = result.replace('</urlset>', section + '\n</urlset>')
    tree = ET.fromstring(result)
    locations = [el.text for el in tree.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    if len(locations) != len(set(locations)):
        raise ValueError("URLs repetidas no sitemap.")
    return result


def plan(root: Path, documents: dict[str, str], today: str) -> tuple[dict[str, str], list[str], dict]:
    previous = load_manifest(root)
    current = inventory(documents, previous, today)
    stale = sorted(set(previous["files"]) - set(documents))
    for path in stale:
        target = root / path
        if not path.startswith(BASE):
            raise ValueError("Uma página fora das listagens não pode ser retirada automaticamente.")
        if not target.resolve().is_relative_to(root.resolve()):
            raise ValueError("Destino de página obsoleta sai do repositório.")
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != previous["files"][path]["sha256"]:
            raise ValueError("Página gerada foi editada localmente; revisar antes de retirar: " + path)
    for path in documents:
        target = root / path
        if not target.resolve().is_relative_to(root.resolve()):
            raise ValueError("Destino de página gerada sai do repositório.")
        if target.exists() and path.startswith(BASE) and path not in previous["files"] and MARKER not in target.read_text():
            raise ValueError("Arquivo existente não pertence ao gerador: " + path)
    outputs = dict(documents)
    outputs[MANIFEST] = json.dumps(current, ensure_ascii=False, indent=2) + '\n'
    outputs['sitemap.xml'] = sitemap_document((root / 'sitemap.xml').read_text(), current)
    return outputs, stale, current


def apply_plan(root: Path, outputs: dict[str, str], stale: list[str]) -> None:
    for path in list(outputs) + stale:
        if not (valid_owned_path(path) or path in {MANIFEST, 'sitemap.xml'}):
            raise ValueError("Arquivo fora do escopo da geração: " + path)
        if not (root / path).resolve().is_relative_to(root.resolve()):
            raise ValueError("Destino fora do repositório: " + path)
    if any(not path.startswith(BASE) for path in stale):
        raise ValueError("Retirada automática permitida apenas para listagens geradas.")
    for path, content in outputs.items():
        output = root / path
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + '.tmp')
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(output)
    for path in stale:
        output = root / path
        if output.exists():
            output.unlink()
