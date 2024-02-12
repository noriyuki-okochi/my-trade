drop table if exists trigger;
create table if not exists trigger( seqnum integer PRIMARY KEY,
                                    symbol text NOT NULL,
                                    trade text NOT NULL,
                                    exchange text,
                                    rate real, 
                                    method text default 'IM',
                                    amount real default 0.0,
                                    count integer DEFAULT 0,
                                    continuing int default 0,
                                    histgram real default 0.0,
                                    updated_at TIMESTAMP DEFAULT(DATETIME('now','localtime'))
                                );
