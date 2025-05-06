-- Atualiza todos os estados para suas respectivas siglas
UPDATE alta_gasstation
SET estado = CASE 
    WHEN UPPER(estado) = 'SAO PAULO' THEN 'SP'
    WHEN UPPER(estado) = 'RIO DE JANEIRO' THEN 'RJ'
    WHEN UPPER(estado) = 'MINAS GERAIS' THEN 'MG'
    WHEN UPPER(estado) = 'ESPIRITO SANTO' THEN 'ES'
    WHEN UPPER(estado) = 'PARANA' THEN 'PR'
    WHEN UPPER(estado) = 'SANTA CATARINA' THEN 'SC'
    WHEN UPPER(estado) = 'RIO GRANDE DO SUL' THEN 'RS'
    WHEN UPPER(estado) = 'MATO GROSSO DO SUL' THEN 'MS'
    WHEN UPPER(estado) = 'MATO GROSSO' THEN 'MT'
    WHEN UPPER(estado) = 'GOIAS' THEN 'GO'
    WHEN UPPER(estado) = 'DISTRITO FEDERAL' THEN 'DF'
    WHEN UPPER(estado) = 'BAHIA' THEN 'BA'
    WHEN UPPER(estado) = 'SERGIPE' THEN 'SE'
    WHEN UPPER(estado) = 'ALAGOAS' THEN 'AL'
    WHEN UPPER(estado) = 'PERNAMBUCO' THEN 'PE'
    WHEN UPPER(estado) = 'PARAIBA' THEN 'PB'
    WHEN UPPER(estado) = 'RIO GRANDE DO NORTE' THEN 'RN'
    WHEN UPPER(estado) = 'CEARA' THEN 'CE'
    WHEN UPPER(estado) = 'PIAUI' THEN 'PI'
    WHEN UPPER(estado) = 'MARANHAO' THEN 'MA'
    WHEN UPPER(estado) = 'PARA' THEN 'PA'
    WHEN UPPER(estado) = 'AMAPA' THEN 'AP'
    WHEN UPPER(estado) = 'AMAZONAS' THEN 'AM'
    WHEN UPPER(estado) = 'RORAIMA' THEN 'RR'
    WHEN UPPER(estado) = 'RONDONIA' THEN 'RO'
    WHEN UPPER(estado) = 'ACRE' THEN 'AC'
    WHEN UPPER(estado) = 'TOCANTINS' THEN 'TO'
    ELSE estado
END;

-- Verifica a distribuição dos estados após a atualização
SELECT estado, COUNT(*) as quantidade
FROM alta_gasstation
GROUP BY estado
ORDER BY quantidade DESC;

-- Exemplos de uso do LIKE para busca que contém texto

-- Buscar postos em Jundiaí que contêm "agapeama" no nome
SELECT *
FROM alta_gasstation
WHERE cidade = 'JUNDIAI'
AND UPPER(razao) LIKE '%AGAPEAMA%';

-- 1. Buscar postos que contêm "PAULO" no nome da razão social
SELECT cnpj, razao, estado
FROM alta_gasstation
WHERE UPPER(razao) LIKE '%PAULO%';

-- 2. Buscar postos que contêm "RIO" no nome da razão social
SELECT cnpj, razao, estado
FROM alta_gasstation
WHERE UPPER(razao) LIKE '%RIO%';

-- 3. Buscar postos que contêm "SANTOS" no nome da razão social
SELECT cnpj, razao, estado
FROM alta_gasstation
WHERE UPPER(razao) LIKE '%SANTOS%';

-- 4. Buscar postos que contêm "POSTO" no nome da razão social
SELECT cnpj, razao, estado
FROM alta_gasstation
WHERE UPPER(razao) LIKE '%POSTO%';

-- 5. Buscar postos que contêm "COMBUSTIVEIS" no nome da razão social
SELECT cnpj, razao, estado
FROM alta_gasstation
WHERE UPPER(razao) LIKE '%COMBUSTIVEIS%';

-- 6. Contar quantos postos contêm "POSTO" no nome
SELECT COUNT(*) as total_postos
FROM alta_gasstation
WHERE UPPER(razao) LIKE '%POSTO%';

-- 7. Buscar postos que contêm "POSTO" e estão em SP
SELECT cnpj, razao, estado
FROM alta_gasstation
WHERE UPPER(razao) LIKE '%POSTO%'
AND estado = 'SP';

-- 8. Buscar postos que contêm "POSTO" ou "COMBUSTIVEIS" no nome
SELECT cnpj, razao, estado
FROM alta_gasstation
WHERE UPPER(razao) LIKE '%POSTO%'
OR UPPER(razao) LIKE '%COMBUSTIVEIS%';

-- 9. Buscar postos que contêm "POSTO" e não contêm "COMBUSTIVEIS"
SELECT cnpj, razao, estado
FROM alta_gasstation
WHERE UPPER(razao) LIKE '%POSTO%'
AND UPPER(razao) NOT LIKE '%COMBUSTIVEIS%';

-- Buscar todos os registros com preço de revenda maior que 5,00
SELECT 
    a.id,
    a.data_coleta,
    g.razao,
    g.cidade,
    g.estado,
    a.produto,
    a.preco_revenda
FROM alta_addprice a
JOIN alta_gasstation g ON a.gasstation_id_id = g.id
WHERE a.preco_revenda > 5.00
ORDER BY a.preco_revenda DESC;

-- Contar quantos registros têm preço maior que 5,00
SELECT COUNT(*) as total_registros
FROM alta_addprice
WHERE preco_revenda > 5.00;

-- Ver distribuição por produto
SELECT 
    produto,
    COUNT(*) as quantidade,
    MIN(preco_revenda) as menor_preco,
    MAX(preco_revenda) as maior_preco,
    AVG(preco_revenda) as media_preco
FROM alta_addprice
WHERE preco_revenda > 5.00
GROUP BY produto
ORDER BY quantidade DESC;

-- Exemplos de JOIN entre alta_gasstation e alta_addprice

-- 1. INNER JOIN (apenas registros que existem em ambas as tabelas)
SELECT 
    g.id as posto_id,
    g.razao,
    g.cidade,
    g.estado,
    a.id as preco_id,
    a.produto,
    a.preco_revenda,
    a.data_coleta
FROM alta_gasstation g
INNER JOIN alta_addprice a ON g.id = a.gasstation_id_id
ORDER BY g.razao, a.data_coleta;

-- 2. LEFT JOIN (todos os postos, mesmo sem preços)
SELECT 
    g.id as posto_id,
    g.razao,
    g.cidade,
    g.estado,
    a.id as preco_id,
    a.produto,
    a.preco_revenda,
    a.data_coleta
FROM alta_gasstation g
LEFT JOIN alta_addprice a ON g.id = a.gasstation_id_id
ORDER BY g.razao, a.data_coleta;

-- 3. RIGHT JOIN (todos os preços, mesmo sem postos)
SELECT 
    g.id as posto_id,
    g.razao,
    g.cidade,
    g.estado,
    a.id as preco_id,
    a.produto,
    a.preco_revenda,
    a.data_coleta
FROM alta_gasstation g
RIGHT JOIN alta_addprice a ON g.id = a.gasstation_id_id
ORDER BY g.razao, a.data_coleta;

-- 4. FULL JOIN (todos os registros de ambas as tabelas)
SELECT 
    g.id as posto_id,
    g.razao,
    g.cidade,
    g.estado,
    a.id as preco_id,
    a.produto,
    a.preco_revenda,
    a.data_coleta
FROM alta_gasstation g
FULL JOIN alta_addprice a ON g.id = a.gasstation_id_id
ORDER BY g.razao, a.data_coleta;

-- 5. JOIN com filtros adicionais
SELECT 
    g.id as posto_id,
    g.razao,
    g.cidade,
    g.estado,
    a.id as preco_id,
    a.produto,
    a.preco_revenda,
    a.data_coleta
FROM alta_gasstation g
INNER JOIN alta_addprice a ON g.id = a.gasstation_id_id
WHERE g.estado = 'SP'
AND a.preco_revenda > 5.00
ORDER BY a.preco_revenda DESC;

-- 6. JOIN com agregação
SELECT 
    g.estado,
    g.cidade,
    COUNT(a.id) as total_precos,
    MIN(a.preco_revenda) as menor_preco,
    MAX(a.preco_revenda) as maior_preco,
    AVG(a.preco_revenda) as media_preco
FROM alta_gasstation g
LEFT JOIN alta_addprice a ON g.id = a.gasstation_id_id
GROUP BY g.estado, g.cidade
ORDER BY g.estado, g.cidade;

-- 7. JOIN com subconsulta
SELECT 
    g.id as posto_id,
    g.razao,
    g.cidade,
    g.estado,
    a.produto,
    a.preco_revenda,
    a.data_coleta
FROM alta_gasstation g
INNER JOIN (
    SELECT *
    FROM alta_addprice
    WHERE preco_revenda > 5.00
) a ON g.id = a.gasstation_id_id
ORDER BY a.preco_revenda DESC; 