-- =====================================================================
-- VALIDAÇÕES COMPLEMENTARES (não fazem parte da apresentação original)
-- Consultas elaboradas depois da apresentação para testar a solidez das
-- conclusões de 01_analise_original.sql. Os resultados, obtidos no banco
-- original, estão em docs/resultados/ e não aparecem nos slides.
-- Mesma tabela: amazon_reviews(star_rating, category, review_date, review_text)
-- =====================================================================

-- C1. Qualidade dos dados: nulos e notas fora da escala
-- Complementa a etapa 1 (Sanity Check): a média e os percentuais só são confiáveis se não há lixo na base.
SELECT
    COUNT(*)                                                        AS total_registros,
    SUM(star_rating IS NULL)                                        AS nota_nula,
    SUM(star_rating IS NOT NULL AND star_rating NOT BETWEEN 1 AND 5) AS nota_fora_de_1_a_5,
    SUM(category IS NULL)                                           AS categoria_nula,
    SUM(review_date IS NULL)                                        AS data_nula,
    SUM(review_text IS NULL OR TRIM(review_text) = '')              AS texto_vazio
FROM amazon_reviews;
-- Objetivo: confirmar que os 100.000 registros são analisáveis (e quantos ficam fora da série temporal).

-- C2. Volume e média por mês
-- A queda de dezembro só é interpretável sabendo o tamanho da amostra de cada mês.
SELECT
    STRFTIME('%Y-%m', review_date) AS mes_ano,
    COUNT(*)                       AS volume,
    ROUND(AVG(star_rating), 3)     AS media_mensal
FROM amazon_reviews
WHERE review_date IS NOT NULL
GROUP BY mes_ano
ORDER BY mes_ano ASC;
-- Objetivo: verificar se a variação mensal vem de meses com volume muito menor.

-- C3. Dezembro vs. resto do ano, por categoria
-- A queda é geral ou localizada em poucas categorias?
SELECT
    category,
    ROUND(AVG(CASE WHEN STRFTIME('%m', review_date) = '12' THEN star_rating END), 3)  AS media_dezembro,
    ROUND(AVG(CASE WHEN STRFTIME('%m', review_date) <> '12' THEN star_rating END), 3) AS media_demais_meses,
    SUM(STRFTIME('%m', review_date) = '12')                                           AS volume_dezembro
FROM amazon_reviews
WHERE review_date IS NOT NULL
GROUP BY category
ORDER BY category;
-- Objetivo: separar efeito sazonal geral de efeito concentrado em categorias específicas.

-- C4. Percentual de detratores (notas 1 e 2) por categoria
-- A média por categoria varia pouco; o percentual de detratores mostra se há diferença de risco.
SELECT
    category,
    COUNT(*)                                                    AS volume,
    ROUND(AVG(star_rating), 3)                                  AS media_avaliacao,
    ROUND(100.0 * SUM(star_rating <= 2) / COUNT(*), 2)          AS pct_detratores
FROM amazon_reviews
GROUP BY category
ORDER BY pct_detratores DESC;
-- Objetivo: checar se 'Health' também lidera em detratores ou se a diferença de média é marginal.

-- C5. Termo 'worth': qual padrão textual está sendo capturado?
-- LIKE '%worth%' casa com 'not worth', 'worthless', 'worthwhile', 'worth it'... com polaridades opostas.
SELECT
    CASE
        WHEN t LIKE '%not worth%' OR t LIKE '%n''t worth%' THEN 'negacao + worth'
        WHEN t LIKE '%worthless%'                          THEN 'worthless'
        WHEN t LIKE '%worthwhile%'                         THEN 'worthwhile'
        ELSE 'outros usos de worth'
    END                          AS padrao,
    COUNT(*)                     AS mencoes,
    ROUND(AVG(star_rating), 2)   AS media_nota
FROM (
    SELECT LOWER(review_text) AS t, star_rating
    FROM amazon_reviews
    WHERE LOWER(review_text) LIKE '%worth%'
)
GROUP BY padrao
ORDER BY mencoes DESC;
-- Objetivo: entender se a média baixa (consulta 7) vem de um padrão negativo específico.

-- C6. Sobreposição entre 'worth' e detratores
-- Mede quanto do grupo 'worth' é, na prática, o próprio grupo de detratores (risco de circularidade).
SELECT
    SUM(w)                                          AS mencoes_worth,
    SUM(w * d)                                      AS mencoes_worth_detratoras,
    ROUND(100.0 * SUM(w * d) / SUM(w), 2)           AS pct_worth_que_sao_detratoras,
    SUM(d)                                          AS total_detratores,
    ROUND(100.0 * SUM(w * d) / SUM(d), 2)           AS pct_detratores_que_citam_worth
FROM (
    SELECT
        COALESCE(LOWER(review_text) LIKE '%worth%', 0) AS w,
        COALESCE(star_rating <= 2, 0)                  AS d
    FROM amazon_reviews
);
-- Objetivo: se ambos os percentuais forem próximos de 100%, 'worth' apenas rotula os detratores e não explica sua causa.
