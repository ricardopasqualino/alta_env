const hasuraEndpoint = 'https://promptql.console.hasura.io/h';

async function conectarIA(pergunta) {
    try {
        const response = await fetch(hasuraEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-hasura-admin-secret': process.env.HASURA_ADMIN_SECRET
            },
            body: JSON.stringify({
                query: pergunta
            })
        });
        return await response.json();
    } catch (error) {
        console.error('Erro na conexão com IA:', error);
        return null;
    }
} 