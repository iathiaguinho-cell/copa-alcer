import pandas as pd
import json
import os
import sys

DATABASE_FILE = 'database.json'
PONTUACAO_GERAL = {
    1: 100, 2: 95, 3: 92, 4: 90, 5: 88,
    6: 86, 7: 84, 8: 82, 9: 80, 10: 78
}
PONTUACAO_PARTICIPACAO = 50

def get_pontos(posicao):
    try:
        pos = int(posicao)
        return PONTUACAO_GERAL.get(pos, PONTUACAO_PARTICIPACAO)
    except (ValueError, TypeError):
        return PONTUACAO_PARTICIPACAO

def carregar_database():
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"campeonato": "Copa Alcer", "atletas": {}}

def salvar_database(data):
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def processar_etapa(filepath, db):
    filename = os.path.splitext(os.path.basename(filepath))[0]
    etapa_nome = filename.split('/')[0].replace("_", " ") # Extrai o nome da etapa do caminho
    
    # Determina gênero e distância a partir do nome do arquivo
    genero = "Masculino" if "masculino" in filename.lower() else "Feminino"
    distancia = "10K" if "10k" in filename.lower() else "5K"

    try:
        df = pd.read_excel(filepath)
        print(f"Processando: {etapa_nome} - {distancia} {genero}")
    except Exception as e:
        print(f"Erro ao ler o arquivo {filepath}: {e}")
        return

    colunas_necessarias = ['Numero', 'Nome', 'Tempo_Liquido', 'Colocacao_Geral']
    if not all(col in df.columns for col in colunas_necessarias):
        print(f"ERRO: Colunas essenciais não encontradas na planilha: {filepath}")
        return

    for _, row in df.iterrows():
        try:
            numero_atleta = str(int(row['Numero']))
            nome_atleta = str(row['Nome']).strip()
            colocacao = int(row['Colocacao_Geral'])
        except (ValueError, TypeError):
            continue

        pontos = get_pontos(colocacao)

        if numero_atleta not in db['atletas']:
            db['atletas'][numero_atleta] = {
                'numero': int(numero_atleta), 'nome': nome_atleta,
                'equipe': str(row.get('Equipe', '')).strip(), 'pontuacao_total': 0, 'corridas': []
            }
        
        db['atletas'][numero_atleta]['nome'] = nome_atleta
        db['atletas'][numero_atleta]['equipe'] = str(row.get('Equipe', '')).strip()

        # Evita duplicar o mesmo resultado de corrida
        if any(c['etapa'] == etapa_nome and c['distancia'] == distancia and c['genero'] == genero for c in db['atletas'][numero_atleta]['corridas']):
            continue

        db['atletas'][numero_atleta]['corridas'].append({
            'etapa': etapa_nome, 'distancia': distancia, 'genero': genero,
            'tempo_liquido': str(row['Tempo_Liquido']), 'colocacao_geral': colocacao,
            'pontos': pontos
        })

def main():
    db = carregar_database()
    arquivo_modificado = sys.argv[1]
    
    if arquivo_modificado.startswith('novas_etapas/') and arquivo_modificado.endswith('.xlsx'):
        processar_etapa(arquivo_modificado, db)
        
        # Recalcula a pontuação geral total para todos os atletas
        for atleta_id in db['atletas']:
            total_pontos = sum(corrida['pontos'] for corrida in db['atletas'][atleta_id]['corridas'])
            db['atletas'][atleta_id]['pontuacao_total'] = total_pontos
        
        salvar_database(db)
        print(f"Processamento concluído! '{DATABASE_FILE}' foi atualizado.")

if __name__ == "__main__":
    main()
