# Artigo de estudo para a normalização desse projeto

Abaixo seguem as tabelas originais antes de qualquer passo de normalização:

### df_tracks:
| track_id          | track_name                     | album_id         | artists_ids                      | images_ids                                                              | explicit | duration_ms | danceability | energy  | key | loudness | mode | speechiness | acousticness | instrumentalness | liveness | valence |
|-------------------|--------------------------------|------------------|----------------------------------|------------------------------------------------------------------------|----------|-------------|--------------|---------|-----|----------|------|-------------|--------------|------------------|----------|---------|
| 6xkYAK0duVMRfWOglN2z3G | Comptine D'un Autre Été      | 4nR3fukS0O34BvxUb4JNJa | ["3T7wt23xNhYheYCCtKKntb"]        | ["aec56705ee1098ee3622c132773d945f","d51d259e43e0326f5418ab06ea380090","78d60a1ff32db1951a1f3974f4149813"] | False    | 122601      | 0.546        | 0.00735 | 3   | -32.851  | 1    | 0.0412      | 0.984        | 0.918              | 0.0994   | 0.128   |
| 3GElbFnmO7zexsPf3Tv9zz | Nocturnes, Op. 9: No. 2 in E-Flat Major | 0H0ySyRhqLmRyX4hRiwM5I | ["7y97mc3bZRFXzT2szRM4L4","0UucWXEyfCOSWlvGQYmPu3"] | ["72374e3017599b693612161224b827f5","c7064fe561bb427c165aa99da970fb8a","da2e3cf681a6e2905b444f1f2981725f"] | False    | 257406      | 0.387        | 0.228   | 3   | -19.412  | 1    | 0.0474      | 0.963        | 0.936              | 0.111    | 0.0985  |
| 6kf7ZCJjEbjZXikivKOsvJ | Clair de lune | 2ytXs8CezH3sgHPrf5sSjc | ["1Uff91EOsvd99rtAupatMP","2fxWL96h0S44PhEa9e6mtm"] | ["eec8c2c605ada67d82a304ad74dfa8cc","2aa7068b2993bcdf75ef8e324274f964","79615daed1247b490c2b5e083f6a7690"] | False    | 347426      | 0.387        | 0.228   | 3   | -19.412  | 1    | 0.0474      | 0.963        | 0.936              | 0.111    | 0.0985  |


### df_artists
| artist_id        | artist_name            |
|------------------|------------------------|
| 3T7wt23xNhYheYCCtKKntb | Yann Tiersen            |
| 7y97mc3bZRFXzT2szRM4L4 | Frédéric Chopin         |
| 0UucWXEyfCOSWlvGQYmPu3 | Various Artists         |

### df_album
| album_id         | album_name              | release_date |
|------------------|-------------------------|--------------|
| 4nR3fukS0O34BvxUb4JNJa | Amélie Soundtrack        | 2001-04-23   |
| 0H0ySyRhqLmRyX4hRiwM5I | Chopin: Nocturnes        | 1960-10-01   |

### df_images
| image_id                              | height | width |
|---------------------------------------|--------|-------|
| aec56705ee1098ee3622c132773d945f      | 640    | 640   |
| d51d259e43e0326f5418ab06ea380090      | 300    | 300   |
| 78d60a1ff32db1951a1f3974f4149813      | 64     | 64    |
| 72374e3017599b693612161224b827f5      | 640    | 640   |
| c7064fe561bb427c165aa99da970fb8a      | 300    | 300   |
| da2e3cf681a6e2905b444f1f2981725f      | 64     | 64    |

## Primeira Forma Normal (1NF)

Em 1NF, cada célula de uma tabela deve conter um único valor atômico, ou seja, não pode conter valores compostos ou repetidos.

Note como em df_tracks, uma linha pode representar diversos artists_ids e images_ids. Sendo assim, na 1FN, cria-se tabelas de relação.

### df_tracks
| track_id          | track_name                     | album_id         | explicit | duration_ms | danceability | energy  | key | loudness | mode | speechiness | acousticness | instrumentalness | liveness | valence |
|-------------------|--------------------------------|------------------|----------|-------------|--------------|---------|-----|----------|------|-------------|--------------|------------------|----------|---------|
| 6xkYAK0duVMRfWOglN2z3G | Comptine D'un Autre Été      | 4nR3fukS0O34BvxUb4JNJa | False    | 122601      | 0.546        | 0.00735 | 3   | -32.851  | 1    | 0.0412      | 0.984        | 0.918              | 0.0994   | 0.128   |

### df_track_artists
| track_id          | artist_id       |
|-------------------|-----------------|
| 6xkYAK0duVMRfWOglN2z3G | 3T7wt23xNhYheYCCtKKntb |


### df_track_images
| track_id          | image_id                          |
|-------------------|-----------------------------------|
| 6xkYAK0duVMRfWOglN2z3G | aec56705ee1098ee3622c132773d945f |
| 6xkYAK0duVMRfWOglN2z3G | d51d259e43e0326f5418ab06ea380090 |
| 6xkYAK0duVMRfWOglN2z3G | 78d60a1ff32db1951a1f3974f4149813 |

## Segunda Forma Normal (2NF)
Em 2NF, uma tabela deve estar na 1NF e todos os seus atributos não chave devem depender completamente da chave primária.

Todas as tabelas respeitam a 2NF.

## Terceira Forma Normal (3NF)
Em 3NF, uma tabela deve estar na 2NF e todos os seus atributos não chave devem depender apenas da chave primária, não de outros atributos não chave.

Todas as tabelas respeitam a 3NF.