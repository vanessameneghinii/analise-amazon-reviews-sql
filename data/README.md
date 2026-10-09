# Dados

O banco original está versionado neste repositório, no arquivo `amazon_customer_reviews_100k.sqlite` desta pasta.

## Banco original

É um conjunto sintético de 100.000 avaliações em SQLite, gerado com o ChatGPT para imitar as avaliações de clientes da Amazon, já que o conjunto original não estava acessível na época. O arquivo usado na análise se chama `amazon_customer_reviews_100k.sqlite` (cerca de 20 MB) e contém a tabela `amazon_reviews`, com 100.000 registros únicos de 2015-01-01 a 2025-12-30.

## Esquema da tabela `amazon_reviews` (13 colunas)

`review_id` TEXT, `product_id` TEXT, `customer_id` TEXT, `category` TEXT, `review_headline` TEXT, `review_text` TEXT, `star_rating` INTEGER, `verified_purchase` INTEGER, `helpful_votes` INTEGER, `thumbs_up` INTEGER, `thumbs_down` INTEGER, `review_date` DATE (guardada como texto ISO) e `review_length` INTEGER.

A análise usa apenas quatro:

| Coluna | Tipo | Observação |
|---|---|---|
| `star_rating` | `INTEGER` | de 1 a 5 |
| `category` | `TEXT` | 10 categorias: Electronics, Books, Home & Kitchen, Clothing, Beauty, Toys & Games, Sports, Grocery, Automotive e Health |
| `review_date` | `TEXT` | formato ISO `AAAA-MM-DD` |
| `review_text` | `TEXT` | texto da avaliação |
