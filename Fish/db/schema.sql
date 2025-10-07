CREATE TABLE IF NOT EXISTS User(
    User_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT NOT NULL,
    Password_Hash TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS Email(
    Email_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    User_ID INTEGER NOT NULL,
    eml_file BLOB, 
    SHA256 TEXT,
    Size_Bytes INTEGER, 
    Received_At TEXT,
    From_Addr TEXT,  
    Tag TEXT, 
    FOREIGN KEY(User_ID) REFERENCES User(User_ID)  
);


CREATE TABLE IF NOT EXISTS Analysis(
    Email_ID INTEGER PRIMARY KEY,
    Score INTEGER,
    Analyzed INTEGER, -- 0 (False) or 1 (True) 
    Verdict TEXT CHECK(Verdict IN ('Phishing', 'Suspicious', 'Benign')),
    Details_json TEXT,  
    Analyzed_At TEXT,
    FOREIGN KEY(Email_ID) REFERENCES Email(Email_ID)
);



