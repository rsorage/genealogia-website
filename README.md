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

```bash
git add -A && git commit -m "atualiza o site" && git push
```

O GitHub Pages republica sozinho em um ou dois minutos. Depois de mudanças grandes, vale reenviar o
`sitemap.xml` no Google Search Console.

---

Texto e pesquisa de Ramon Sorage.
