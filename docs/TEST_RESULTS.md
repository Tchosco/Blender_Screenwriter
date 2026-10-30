# Evidências do M1

Sessão de implementação de 29/10/2026 (America/Sao_Paulo).

| Verificação | Resultado |
|---|---|
| Python 3.12, unittest | 7 testes passaram |
| Blender 5.2.3 LTS, build e13b728c6880 | Executável local confirmado |
| Registro, desregistro e novo registro do add-on | Passou |
| Adaptação legada to_scenes | 1 cena e 4 diálogos |
| Operadores Generate M1 3D e Generate Movie em Text Editor | Ambos passaram após correção do contexto da timeline |
| Cena padrão 40 s / 24 fps | Estrutura de 960 quadros, 2 personagens, 3 câmeras validada |
| Preservação | Criar duas cenas M1 preservou a cena ativa e seus objetos |
| Movimento | Mudança de posição avaliada entre quadros 1 e 100 |
| MP4 Workbench, 30 s, 12 fps, 320×180 | Render completo passou; arquivo de 178.519 bytes |
| Releitura do MP4 pelo Blender | 360 quadros, 12 fps, 30,0 segundos |
| Decodificação de amostras | Quadros 1, 83, 150, 221, 293 e 360 gravados como PNG |
| Inspeção visual | Quadros 1, 83, 150 e 360: estúdio, atores e enquadramentos visíveis |
| Render completo padrão 40 s / 24 fps / 640×360 | Não concluído: falta de espaço no disco C: antes da renderização |

A primeira tentativa de MP4 falhou porque a API de saída do Blender 5.2 exige media_type VIDEO antes de FFMPEG. O relatório dessa tentativa registrou status failed e render_completed false. A segunda tentativa passou após a correção.

Um teste de movimento inicialmente avaliou uma cena não ativa; o teste foi corrigido para ativar a cena antes de avaliar o depsgraph. A geração em si não foi alterada por esse ajuste.

O primeiro teste do botão legado encontrou set_range_to_strips indisponível no contexto Text Editor. O intervalo agora é calculado diretamente pelos strips, e a repetição do teste passou.

Não foram testados instalação via diálogo gráfico, som, render EEVEE/Cycles, exportações PDF/FDX/HTML, Mindmap ou todos os caminhos de palavras-chave/multicâmera. A verificação do MP4 decodifica seis amostras, não todos os quadros.

As evidências locais entregues incluem studio.blend, movie.mp4, movie.srt, report.json, verification.json e as imagens decodificadas. Os arquivos binários de demonstração não são adicionados ao histórico Git.
