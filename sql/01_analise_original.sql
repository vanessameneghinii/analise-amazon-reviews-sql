-- 1. Exploração da Arquitetura do Banco
-- Verificação inicial da estrutura para validar a integridade do ambiente SQLite.
SELECT name 
FROM sqlite_master 
WHERE type='table';
-- Objetivo: Confirmar a presença da tabela 'amazon_reviews' antes de iniciar a extração.

-- 2. Validação de Escala (Volume)
-- Confirmação da robustez amostral para garantir significância estatística.
SELECT COUNT(*) AS total_registros 
FROM amazon_reviews;
-- Objetivo: Validar o universo de 100.000 registros para uma análise confiável.

-- 3. Métrica de Saúde (Média Geral)
-- Definição do Baseline (Linha de Base) de satisfação do ecossistema.
SELECT AVG(star_rating) AS media_geral 
FROM amazon_reviews;
-- Objetivo: Estabelecer o benchmark de 3.96 como métrica de sucesso comparativa.

-- 4. Análise de Risco (Distribuição de Notas)
-- Identificação da polarização de sentimentos com cálculo percentual dinâmico.
SELECT 
    star_rating, 
    COUNT(*) AS volume_notas, 
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM amazon_reviews)), 2) AS percentual 
FROM amazon_reviews 
GROUP BY star_rating 
ORDER BY star_rating DESC;
-- Objetivo: Quantificar o grupo de detratores (notas 1 e 2) para gestão de risco de churn.

-- 5. Benchmarking de Categorias – Identificando a Excelência
-- Ranking de performance para identificar padrões de sucesso (Benchmarks internos).
SELECT 
    category, 
    AVG(star_rating) AS media_avaliacao, 
    COUNT(*) AS volume
FROM amazon_reviews
GROUP BY category
HAVING volume > 1000  -- Filtro de relevância para evitar distorções por baixo volume
ORDER BY media_avaliacao DESC; 
-- Objetivo: Contrastar a excelência de 'Grocery' (3.98) com oportunidades de ajuste em 'Health' (3.93).

-- 6. Série Temporal: Evolução Mensal da Satisfação
-- Monitoramento de tendências sazonais e estabilidade da operação.
SELECT 
    STRFTIME('%Y-%m', review_date) AS mes_ano, 
    AVG(star_rating) AS media_mensal 
FROM amazon_reviews 
WHERE review_date IS NOT NULL 
GROUP BY mes_ano 
ORDER BY mes_ano ASC;
-- Objetivo: Identificar flutuações sazonais, como o recuo pontual observado em dezembro.

-- 7. Investigação de Causa-Raiz: Percepção de Valor
-- Cruzamento de dados quantitativos com insights qualitativos (Text Mining).
SELECT 
    COUNT(*) AS total_mencoes, 
    AVG(star_rating) AS media_nota_insatisfacao
FROM amazon_reviews
WHERE LOWER(review_text) LIKE '%worth%';
-- Objetivo: Validar se a variação nas notas está atrelada à percepção de custo-benefício (Causa-Raiz).