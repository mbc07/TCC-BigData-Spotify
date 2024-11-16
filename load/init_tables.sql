CREATE TABLE album (
    album_id TEXT PRIMARY KEY,
    album_name TEXT NOT NULL,
    release_date DATE
);

CREATE TABLE artists (
    artist_id TEXT PRIMARY KEY,
    artist_name TEXT NOT NULL
);

CREATE TABLE images (
    image_id TEXT PRIMARY KEY,
    height INTEGER DEFAULT 0,
    width INTEGER DEFAULT 0,
    url TEXT NOT NULL
);

CREATE TABLE tracks (
    track_id TEXT PRIMARY KEY,
    track_name TEXT NOT NULL,
    album_id TEXT REFERENCES album(album_id),
    genre TEXT NOT NULL,
    explicit BOOLEAN DEFAULT false,
    duration_ms INTEGER DEFAULT 0,
    popularity INTEGER DEFAULT 0,
    danceability REAL DEFAULT 0,
    energy REAL DEFAULT 0,
    key INTEGER DEFAULT 0,
    loudness REAL DEFAULT 0,
    mode INTEGER DEFAULT 0,
    speechiness REAL DEFAULT 0,
    acousticness REAL DEFAULT 0,
    instrumentalness REAL DEFAULT 0,
    liveness REAL DEFAULT 0,
    valence REAL DEFAULT 0,
    tempo REAL DEFAULT 0,
    time_signature INTEGER DEFAULT 0
);

CREATE TABLE artist_track (
    track_id TEXT REFERENCES tracks(track_id),
    artist_id TEXT REFERENCES artists(artist_id),
    PRIMARY KEY (track_id, artist_id)
);

CREATE TABLE image_track (
    track_id TEXT REFERENCES tracks(track_id),
    image_id TEXT REFERENCES images(image_id),
    PRIMARY KEY (track_id, image_id)
);
