# genealogia-website

O site publicado em **https://genealogia.rsorage.com** — a história da pesquisa genealógica das
famílias **Cardillo** e **Sorage**, de Padula e Messina a Minas Gerais.

Serve também de caderno: a parte final da página é um diário de pesquisa com entradas datadas, que
muda à medida que os documentos aparecem. O histórico de commits deste repositório é, portanto, o
histórico de edições do caderno.

## O que há aqui

| arquivo | o que é |
|---|---|
| `index.html` | a página inteira, autocontida: texto, estilos e imagens (WebP) num arquivo só |
| `capa.jpg` | a imagem que aparece quando o link é compartilhado (`og:image`, 1200×630) |
| `404.html` | página de erro |
| `CNAME` | o domínio do GitHub Pages. **Não apagar** — sem ele o domínio se desassocia |
| `.nojekyll` | desliga o processamento Jekyll do GitHub Pages |

A página é estática e não depende de nenhum recurso externo: abre offline, com duplo clique, e
continuará abrindo daqui a vinte anos. A hospedagem é conveniência; o arquivo é o acervo.

## De onde vem o conteúdo

Este repositório **não é onde a página é escrita**. Ele guarda apenas o resultado. A pesquisa, os
documentos e as fichas ficam num arquivo privado, fora daqui, e a página é copiada de lá por um
script de publicação.

> **Regra desta pasta:** só entram os arquivos listados na tabela acima. Nenhum documento de
> família, nenhuma certidão, nenhuma ficha de pesquisa. Este repositório é público e o histórico do
> git é permanente — um arquivo com dados de pessoas vivas que entre aqui não sai mais, mesmo
> apagado num commit seguinte.

## Publicando

```bash
git add -A && git commit -m "atualiza a página" && git push
```

O GitHub Pages republica sozinho em um ou dois minutos.

---

Texto e pesquisa de Ramon Sorage.
