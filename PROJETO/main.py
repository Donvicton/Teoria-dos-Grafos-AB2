import sys
import itertools
import subprocess # Para a função de instalação

# --- Função de Instalação (Bônus) ---
def instalar_bibliotecas():
    """
    Tenta instalar as bibliotecas necessárias (shapely, networkx, matplotlib)
    usando o pip.
    """
    print("Verificando e instalando bibliotecas necessárias...")
    try:
        # sys.executable é o caminho para o interpretador Python atual
        subprocess.check_call([sys.executable, "-m", "pip", "install", "shapely", "networkx", "matplotlib"])
        print("Bibliotecas instaladas/verificadas com sucesso.\n")
    except Exception as e:
        print(f"Erro ao instalar bibliotecas: {e}")
        print("Por favor, instale manualmente no seu terminal:")
        print("pip install shapely networkx matplotlib")
        sys.exit(1)

# --- Importações Principais ---
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon
    from shapely.geometry import Point, LineString, Polygon
except ImportError:
    # Se a instalação falhar ou as bibliotecas não forem encontradas,
    # esta função tentará instalá-las.
    instalar_bibliotecas()
    import networkx as nx
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon
    from shapely.geometry import Point, LineString, Polygon


# --- Passo 2 (Parte A): Leitura do Mapa ---
def ler_mapa(nome_arquivo):
    """Lê o arquivo de mapa e retorna os pontos e obstáculos."""
    print(f"Lendo o arquivo de mapa: {nome_arquivo}...")
    
    vertices_grafo = []      # Todos os nós (quinas, início, fim)
    obstaculos_poligonos = [] # Lista de polígonos (shapely)
    
    with open(nome_arquivo, 'r') as f:
        # 1. Ponto Inicial (q_start)
        linha_start = f.readline().strip().split(',')
        q_start = (float(linha_start[0]), float(linha_start[1]))
        vertices_grafo.append(q_start)
        
        # 2. Ponto Final (q_goal)
        linha_goal = f.readline().strip().split(',')
        q_goal = (float(linha_goal[0]), float(linha_goal[1]))
        vertices_grafo.append(q_goal)
        
        # 3. Número de Obstáculos
        num_obstaculos = int(f.readline().strip())
        
        # 4. Loop pelos obstáculos
        for _ in range(num_obstaculos):
            num_quinas = int(f.readline().strip())
            quinas_obst_atual = []
            
            for _ in range(num_quinas):
                linha_quina = f.readline().strip().split(',')
                quina = (float(linha_quina[0]), float(linha_quina[1]))
                quinas_obst_atual.append(quina)
                vertices_grafo.append(quina)
                
            # Cria o polígono com as quinas
            obst_poly = Polygon(quinas_obst_atual)
            obstaculos_poligonos.append(obst_poly)
            
    print("Leitura concluída.")
    return q_start, q_goal, vertices_grafo, obstaculos_poligonos

# --- Passo 2 (Parte B): Criação do Grafo de Visibilidade ---
def criar_grafo_visibilidade(vertices, obstaculos):
    """Cria o grafo de visibilidade checando a regra de interseção."""
    print("Criando o Grafo de Visibilidade...")
    
    G = nx.Graph()
    
    # Gera todas as combinações únicas de pares de vértices
    for v_i, v_j in itertools.combinations(vertices, 2):
        linha = LineString([v_i, v_j])
        bloqueado = False
        
        # A "regra" é checar se a linha cruza o *interior* de algum obstáculo
        for obst_poly in obstaculos:
            if linha.crosses(obst_poly):
                bloqueado = True
                break
        
        if not bloqueado:
            # O custo (peso) é a distância Euclidiana
            distancia = linha.length
            G.add_edge(v_i, v_j, weight=distancia)
            
    print(f"Grafo de visibilidade criado com {G.number_of_nodes()} nós e {G.number_of_edges()} arestas.")
    return G

# --- Passo 3: Implementar Kruskal ou Prim ---
def calcular_mst(grafo_visibilidade):
    """Calcula a Árvore Geradora Mínima (MST) usando Kruskal."""
    print("Calculando a Árvore Geradora Mínima (MST) com Kruskal...")
    T = nx.minimum_spanning_tree(grafo_visibilidade, algorithm="kruskal")
    print(f"MST calculada. A árvore tem {T.number_of_edges()} arestas.")
    return T

# --- Passo 4: Implementação da função verticeMaisProximo ---
def vertice_mais_proximo(posicao, arvore):
    """Encontra o vértice da árvore mais próximo de uma dada posição."""
    ponto = Point(posicao)
    vertice_perto = None
    dist_minima = float('inf')
    
    for v_coords in arvore.nodes():
        v_ponto = Point(v_coords)
        dist = ponto.distance(v_ponto)
        
        if dist < dist_minima:
            dist_minima = dist
            vertice_perto = v_coords
            
    return vertice_perto

# --- Passo 5: Implementação de algoritmo de busca na árvore ---
def buscar_caminho(q_start, q_goal, arvore):
    """Encontra o caminho na árvore do vértice mais próximo do início ao fim."""
    print("Buscando caminho na árvore...")
    
    v_inicial = vertice_mais_proximo(q_start, arvore)
    v_final = vertice_mais_proximo(q_goal, arvore)
    
    print(f"  - Vértice mais próximo do Início: {v_inicial}")
    print(f"  - Vértice mais próximo do Fim: {v_final}")
    
    try:
        caminho_vertices = nx.shortest_path(arvore, source=v_inicial, target=v_final, weight="weight")
        print("  - Caminho encontrado.")
    except nx.NetworkXNoPath:
        print("  - ERRO: Não foi encontrado caminho entre os vértices.")
        return []
    
    caminho_completo = [q_start] + caminho_vertices + [q_goal]
    return caminho_completo

# --- Passo 6: Plotar o caminho gerado no mapa ---
def plotar_caminho(q_start, q_goal, obstaculos, arvore_mst, caminho, nome_saida="resultado.png"):
    """Plota o mapa, obstáculos, a MST e o caminho encontrado."""
    print(f"Plotando o resultado e salvando em '{nome_saida}'...")
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 1. Plotar Obstáculos
    for poly in obstaculos:
        ax.add_patch(MplPolygon(poly.exterior.coords, facecolor='gray', edgecolor='black', alpha=0.7))
        
    # 2. Plotar a Árvore Geradora Mínima (MST)
    for (u, v) in arvore_mst.edges():
        ax.plot([u[0], v[0]], [u[1], v[1]], color='cyan', linestyle='--', linewidth=0.7)

    # 3. Plotar o Caminho Encontrado
    if caminho:
        x_coords = [p[0] for p in caminho]
        y_coords = [p[1] for p in caminho]
        ax.plot(x_coords, y_coords, marker='o', color='blue', linestyle='-', linewidth=2, label='Caminho')
        
    # 4. Plotar pontos de Início e Fim
    ax.scatter(q_start[0], q_start[1], color='green', s=150, label='Início (q_start)', zorder=5)
    ax.scatter(q_goal[0], q_goal[1], color='red', s=150, label='Fim (q_goal)', zorder=5)
    
    ax.legend()
    ax.set_title("Grafo de Visibilidade, MST e Caminho do Robô")
    ax.set_xlabel("Posição X")
    ax.set_ylabel("Posição Y")
    ax.set_aspect('equal')
    plt.grid(True, linestyle=':', alpha=0.6)
    
    plt.savefig(nome_saida)
    print("Plotagem salva.")
    # plt.show() # Descomente esta linha se quiser que o gráfico apareça

# --- Bloco de Execução Principal ---
if __name__ == "__main__":
    # Primeiro, tenta instalar as dependências
    instalar_bibliotecas()

    # Verifica se o nome do arquivo de mapa foi passado
    if len(sys.argv) != 2:
        print("Erro: Forneça o nome do arquivo de mapa como argumento.")
        print("Exemplo: python main.py mapa.txt")
        sys.exit(1)
        
    arquivo_mapa = sys.argv[1]
    
    try:
        # Passos 2-6
        start, goal, vertices, obstaculos = ler_mapa(arquivo_mapa)
        grafo_vis = criar_grafo_visibilidade(vertices, obstaculos)
        mst = calcular_mst(grafo_vis)
        caminho_final = buscar_caminho(start, goal, mst)
        plotar_caminho(start, goal, obstaculos, mst, caminho_final)
        
        print("\nTrabalho concluído com sucesso!")

    except FileNotFoundError:
        print(f"Erro: Arquivo '{arquivo_mapa}' não encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")