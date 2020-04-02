# pyimagesort
Classifique arquivos de imagem e vídeo, remova duplicatas

### Baixar

https://github.com/monospacesoftware/pyimagesort/releases

### Recursos

* Capaz de processar jpg, png, mov, avi, mp4, wmv, m4v.
* Classifica os arquivos no diretório de destino, criando subdiretórios por ano e mês.
* Os arquivos são nomeados usando o carimbo de data / hora mais antigo encontrado no arquivo, por exemplo, `/ classificado / 2017/08 / 20170801-193758-0.jpg`
* Utiliza o sistema de arquivos e todos os carimbos de data / hora EXIF ​​disponíveis para tentar determinar o carimbo de data / hora original (mais antigo)
* As imagens duplicadas são detectadas usando-se por correspondência difusa, com rotação.
* As imagens que foram redimensionadas, giradas, muito ligeiramente alteradas ou são quase idênticas serão consideradas correspondentes.
* Mantém sempre a versão de resolução mais alta das imagens correspondentes.
* Se duas imagens corresponderem e tiverem a mesma resolução, manterá a versão HDR.
* Preservará o EXIF ​​da imagem mais antiga, mesmo que a mais antiga tenha resolução mais baixa e não seja mantida.
* Exclui imagens duplicadas apenas se uma correspondência exata foi detectada. Caso contrário, é feito o backup das imagens em um diretório da lixeira.
* Ignora diretórios começando com. (ponto).
* Remove diretórios esvaziados como resultado da classificação.

### Requisitos

* Python 3.6 ou superior
* [exiftool] (https://www.sno.phy.queensu.ca/~phil/exiftool/)

### Instalação

* Descompacte em qualquer diretório
* `pip install -r requirements.txt`

### Uso

`fonte de destino sort.py [fonte ...]`

* `destination` é o caminho completo para um diretório para classificar as imagens
* `source` é o caminho completo para diretórios que contêm imagens para processar

### Notas

* Um diretório chamado `.imagesort /` será criado no diretório `destination`, usado para armazenar o banco de dados de imagens.
* As imagens duplicadas serão copiadas para `.imagesort / trash`. Você pode excluí-los conforme desejado.
* Na inicialização, o banco de dados é verificado quanto à consistência com o diretório `destination` e criado ou corrigido com base nas imagens que este diretório contém.
* Você deve tentar evitar modificar o diretório `destination` depois que as imagens forem classificadas.
* Você pode ajustar o limite da correspondência difusa alterando SIMILAR_IMAGE_HASH_DIST no ImageSorter.py.
  * Faixa 0-1024, padrão 3
  * 0 = Correspondência exata
  * 3 é conservador, você pode ir até 5 ou 6. Quanto mais alto, mais correspondências falsas você terá e corre o risco de perder as imagens que deseja manter.
  

### Bugs conhecidos, TODOs

* Rotação automática para orientação adequada
* Os arquivos de vídeo não usam correspondência difusa

### Autor

[Paul Cowan] (paul@monospacesoftware.com) ([Monospace Software LLC] (https://monospacesoftware.com/))
