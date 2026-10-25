# genealogia-website

O site publicado em **https://genealogia.rsorage.com**: a genealogia das famílias **Sorage** (Suraci, de
Laganadi, na Calábria) e **Cardillo** (de Battaglia, na província de Salerno), imigrantes italianos em
Carangola e Patrocínio do Muriaé, Minas Gerais.

Serve também de caderno: as páginas mudam à medida que os documentos aparecem, inclusive quando mostram
que estávamos errados. O histórico de commits deste repositório é, portanto, o histórico de edições do
caderno.

## O que há aqui

| arquivo | o que é |
|---|---|
| `index.html` | o portal: as duas linhas da família, a história, o método, as novidades e o contato |
| `suraci/index.html` | a linha Suraci → Sorage (Laganadi → Carangola), com fontes e graus de certeza |
| `suraci/it/index.html`, `suraci/en/index.html` | resumos da linha Suraci em italiano e em inglês |
| `cardillo/index.html` | a linha Cardillo → Cardilo (Battaglia → Patrocínio do Muriaé), com os avós dos dois lados e a linha até Padula |
| `cardillo/it/index.html`, `cardillo/en/index.html` | resumos da linha Cardillo em italiano e em inglês |
| `historia/index.html` | a história da pesquisa desde 2005 e o caderno de entradas datadas (antes era a página inicial) |
| `metodo/index.html` | como pesquisamos: graus de certeza, regras, fontes, imagens e privacidade |
| `registros-vistos/index.html` | catálogo público gerado dos nomes transcritos e páginas consultadas, com busca, filtros e links para os originais |
| `registros-vistos/catalogo/` | índice de listagens e páginas por localidade, série e ano, com os nomes diretamente no HTML |
| `scripts/exportar-registros.py` | exportador local; lê o acervo privado e prepara as páginas e o sitemap, sem publicar |
| `scripts/catalogo_estatico.py` | geração das listagens, endereços próprios e controle de arquivos gerados |
| `scripts/consolidar-scilla.py` | consolidação específica da amostra de Scilla no índice privado, com rastreio e sem duplicar importações |
| `scripts/registros-vistos/` | modelo, notas públicas revisadas e inventário público `gerados.json` (assinaturas e datas das páginas); editar o modelo e as notas, não os arquivos gerados |
| `tests/test_exportar_registros.py` | verificações da seleção pública e da exportação |
| `tests/test_consolidar_scilla.py` | verificações de preservação, papéis, dúvidas e repetição do lote de Scilla |
| `tests/test_catalogo_estatico.py` | verificações dos nomes no HTML, metadados, links e retirada segura de listagens obsoletas |
| `catasto-1749.html` | os três núcleos Cardillo no Catasto Onciario de Padula, 1749 |
| `capa.jpg` | a imagem de compartilhamento da página da história (`og:image`, 1200×630) |
| `assets/og/` | as imagens de compartilhamento do portal e das linhas Suraci e Cardillo: cartões tipográficos, sem documento |
| `assets/catasto-1749/` | os recortes do Catasto usados em `catasto-1749.html` |
| `robots.txt`, `sitemap.xml` | para os buscadores |
| `404.html` | página de erro |
| `CNAME` | o domínio do GitHub Pages. **Não apagar**: sem ele o domínio se desassocia |
| `.nojekyll` | desliga o processamento Jekyll do GitHub Pages |

Cada página é estática e autocontida: texto e estilos num arquivo só, sem nenhum recurso externo. Cada
uma abre sozinha, offline. Os links entre páginas usam endereços do site (`/suraci/`), então, para
navegar entre elas no computador, sirva a pasta:

```bash
python3 -m http.server 8000   # e abra http://localhost:8000
```

## De onde vem o conteúdo

A pesquisa, os documentos e as fichas ficam num arquivo privado, fora daqui. O que entra neste
repositório é só o resultado.

> **Regras desta pasta.** Este repositório é público e o histórico do git é permanente: um arquivo que
> entre aqui não sai mais, mesmo apagado num commit seguinte.
>
> - Só entram os arquivos listados na tabela acima. Nenhuma certidão, nenhuma ficha de pesquisa.
> - **Nenhum nome de pessoa viva**, nenhum número de documento pessoal, nenhuma causa de morte.
> - **Nenhuma imagem de documento nas páginas novas.** Cada arquivo tem suas regras (o FamilySearch
>   proíbe republicar imagens; o arquivo diocesano de Reggio Calabria pede que as cópias não sejam
>   divulgadas; muitos Archivi di Stato pedem uma comunicação antes). As páginas citam trechos transcritos e
>   levam, por links, às imagens nos portais oficiais.

## Publicando

### Atualizando o catálogo Registros vistos

A fonte de trabalho continua no acervo privado, nos arquivos
`01 Indice/registros-vistos/mapa-imagens.csv` e `linhas-transcritas.csv`.
Não copiar esses arquivos para este repositório.

Com as duas pastas lado a lado, execute na raiz deste repositório:

```bash
python3 scripts/exportar-registros.py
```

Se o acervo estiver em outra pasta, acrescente `--acervo /caminho/para/family-research`.
O exportador usa apenas a biblioteca padrão do Python e não faz consultas à rede.
Gera `registros-vistos/index.html`, o índice `registros-vistos/catalogo/index.html`
e as listagens por localidade, série e ano; atualiza também o `sitemap.xml`.
Funciona sem servidor de aplicação ou dependências externas. O layout e o comportamento
da busca ficam em `scripts/registros-vistos/pagina.html`; as listagens são montadas por
`scripts/catalogo_estatico.py` com a mesma identidade visual. **Não editar o HTML gerado**.

Para a amostra de Scilla de 1884, autorizada por Ramon em 25/10/2026, a consolidação
anterior à exportação tem comandos próprios:

```bash
python3 scripts/consolidar-scilla.py --verificar
python3 scripts/consolidar-scilla.py
python3 scripts/exportar-registros.py
```

A opção `--verificar` da consolidação retorna 1 se há menções por incorporar; 0 se
todas já estão no central. O comando preserva o CSV de origem, as entradas e ids
anteriores e guarda cópia e rastreio no acervo privado, em
`01 Indice/registros-vistos/lotes/scilla-amostra-nati-1884/`. Não incorpora outros
arquivos por varredura. Sem grau individual de leitura no original, o lote permanece
provisório; dúvidas explícitas e trechos parciais ficam assinalados. Não inferir
filiação do declarante, parentesco entre participantes ou sobrenomes de crianças.

A exportação:

- seleciona apenas anos explícitos e intervalos inteiramente até 1925, com links HTTPS
  para imagens nos portais oficiais aceitos (incluindo a Gazzetta Ufficiale);
- confere também as datas de eventos transcritos, conserva grafias e sinais de dúvida
  e distingue grau de leitura de cobertura da consulta;
- exporta uma lista explícita de campos; não copia as colunas `obs`, `ficha`, `lido_por`,
  `idade` ou `residencia`, nem campos internos de lote, origem, linha e SHA-256;
- resume o conteúdo das páginas por regras estruturais, sem copiar nomes e anotações
  marginais dos campos livres. Informações posteriores ao corte podem existir nas imagens
  originais, mas não entram nessas descrições;
- agrupa revisitas à mesma imagem, sem inferir leitura integral. Fotos diferentes de
  uma mesma folha continuam sendo imagens diferentes;
- preserva os identificadores `L-…` das ocorrências e gera identificadores `P-…`
  estáveis para as páginas, usados nos links individuais. Agrupa nomes de um ato por
  referência documental (separando parte, série, ano e volume); isso não funde pessoas;
- informa entradas novas, alteradas e removidas. O relatório detalhado e os motivos de
  exclusão ficam **no acervo privado**, em `registros-vistos/relatorio-exportacao.json`.

Notas adicionais destinadas ao público ficam em
`scripts/registros-vistos/notas-publicas.json`, por identificador da ocorrência. Esse
arquivo é público: incluir apenas texto revisado para publicação. Um identificador
ausente ou excluído da exportação interrompe a geração, para evitar notas associadas
ao registro errado. Para omitir uma pessoa viva identificada ou outra entrada inadequada,
criar **no acervo privado**, ao lado dos CSV, um `publicacao.json` com
`{"ocultar_ocorrencias": ["L-0001"], "ocultar_paginas": []}` (os identificadores são
exemplos). O arquivo é opcional; nunca copiá-lo para o site. Se houver nota pública
para uma ocorrência omitida, removê-la também; a exportação para até corrigir essa
inconsistência. A antiguidade do ato não prova por si só o falecimento.

Antes de publicar, conferir:

```bash
python3 -m unittest discover -s tests
python3 scripts/exportar-registros.py --verificar
python3 -m http.server 8000
```

Abrir `http://localhost:8000/registros-vistos/`. O modo `--verificar` não grava:
retorna 0 quando todas as páginas, o inventário e o sitemap correspondem aos CSV e ao modelo; 1 quando precisa regenerar;
2 em caso de erro. A busca inclui pais e cônjuge, ignora acentos e pode incluir as
variantes indicadas de sobrenomes. Filtros ficam no endereço da página; os links
de cada ocorrência levam à sua transcrição na listagem estática correspondente. Endereços
antigos com `#L-…` na busca continuam abrindo seus detalhes. Atualizar o catálogo prepara arquivos locais;
a publicação continua pelo fluxo abaixo.

### Listagens e indexação

A busca usa JavaScript para filtrar e paginar. As listagens em
`/registros-vistos/catalogo/<localidade>/<serie>/<ano>/` contêm todas as ocorrências
daquele recorte no próprio HTML, sem paginação ou execução de JavaScript. Tanto a busca
quanto o índice oferecem links comuns para elas. Uma listagem não afirma que o livro
ou ano inteiro tenha sido transcrito; o aviso de cobertura parcial e os graus de leitura
aparecem também para quem chega diretamente pelo Google.

Cada listagem tem título, descrição, endereço canônico próprio e dados estruturados de
navegação (`BreadcrumbList`). O sitemap inclui apenas os endereços permanentes, sem
combinações de filtros. As variações de busca conservam o canônico da página principal.
Não há marcação de pessoas ou parentescos inferidos.

O mesmo comando de exportação atualiza as listagens quando os CSV crescem. O inventário
`scripts/registros-vistos/gerados.json` guarda assinaturas do conteúdo e a data da última
alteração de cada página: uma execução sem mudanças não altera as datas do sitemap.
Se todas as ocorrências de um recorte forem retiradas da seleção pública, sua página
gerada e sua entrada no sitemap são removidas. O gerador interrompe essa retirada se
o arquivo tiver sido editado à mão e protege arquivos alheios às listagens. Incluir
também essas remoções no próximo commit da publicação.

Depois de publicar, conferir no Google Search Console o sitemap e uma listagem de exemplo
pela inspeção de URL; solicitar indexação se necessário. Preparar as páginas não equivale
a publicá-las nem garante inclusão ou posição nos resultados do Google.

### Enviando uma versão revisada ao GitHub

Depois da revisão e quando Ramon pedir a publicação, selecionar apenas os arquivos
da alteração, criar o commit e enviá-lo ao GitHub. O exportador não executa Git.

```bash
git add <arquivos-revisados>
git commit -m "atualiza o site"
git push
```

O GitHub Pages republica sozinho em um ou dois minutos. Depois de mudanças grandes, vale reenviar o
`sitemap.xml` no Google Search Console.

---

Texto e pesquisa de Ramon Sorage.
