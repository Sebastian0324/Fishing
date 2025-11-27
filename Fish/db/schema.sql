CREATE TABLE IF NOT EXISTS User(
    User_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT NOT NULL,
    Password_Hash TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS Email(
    Email_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    User_ID INTEGER NOT NULL,
    Eml_file BLOB, 
    SHA256 TEXT,
    Size_Bytes INTEGER, 
    Received_At TEXT,
    From_Addr TEXT,  
    Tag TEXT,
    Sender_IP TEXT,
    Title TEXT,
    Body_Text TEXT,
    Extracted_URLs TEXT,
    Email_Description TEXT,
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



-- Viktigt för att FK ska fungera i SQLite
PRAGMA foreign_keys = ON;

-- ===== DISCUSSION =====
CREATE TABLE IF NOT EXISTS "Discussion" (
  Discussion_ID  INTEGER PRIMARY KEY,
  Email_ID       INTEGER NOT NULL,
  Title          TEXT    NOT NULL CHECK (length(Title) BETWEEN 1 AND 200),
  Text           TEXT    NOT NULL,
  Created_At     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  Updated_At     DATETIME,
  FOREIGN KEY (Email_ID)
    REFERENCES "Email"(Email_ID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT   -- inget raderingsflöde nu
);

CREATE INDEX IF NOT EXISTS idx_discussion_email   ON "Discussion"(Email_ID);
CREATE INDEX IF NOT EXISTS idx_discussion_created ON "Discussion"(Created_At);

CREATE TRIGGER IF NOT EXISTS trg_discussion_set_updated
AFTER UPDATE ON "Discussion"
FOR EACH ROW
WHEN NEW.Updated_At IS NULL
BEGIN
  UPDATE "Discussion"
  SET Updated_At = CURRENT_TIMESTAMP
  WHERE Discussion_ID = NEW.Discussion_ID;
END;

-- ===== COMMENT =====
CREATE TABLE IF NOT EXISTS "Comment" (
  Comment_ID     INTEGER PRIMARY KEY,
  Discussion_ID  INTEGER NOT NULL,
  User_ID        INTEGER NOT NULL,
  Reference      TEXT,
  Text           TEXT    NOT NULL,
  Created_At     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (Discussion_ID)
    REFERENCES "Discussion"(Discussion_ID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (User_ID)
    REFERENCES "User"(User_ID)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_comment_discussion ON "Comment"(Discussion_ID);
CREATE INDEX IF NOT EXISTS idx_comment_user       ON "Comment"(User_ID);
CREATE INDEX IF NOT EXISTS idx_comment_created    ON "Comment"(Created_At);

INSERT OR IGNORE INTO User (User_ID, Username, Password_Hash)
VALUES (1, 'anonymous', '!!SYSTEM!!');
