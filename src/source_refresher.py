import time
import mysql.connector
from mysql.connector import Error

# komentar da se zlorijan sjeti toga, kaže da je vrlo deskriptivno
from components import help
from api.youtube import YouTubeInfo
from settings import HOST_NAME, USER_NAME, USER_PASSWORD, DB_NAME, PORT_NUMBER


LOOP_INTERVAL = 2 * 3600
CHECKING_INTERVAL = 3 * 3600
EXPIRY_TIME = 5 * 3600


class SqlException(Exception):
    def __init__(self, description: str):
        print(f'Database query failed. Description: {description}')


class SourceRefresher:
    def __init__(self):
        self.connection = None
        try:
            self.connection = mysql.connector.connect(
                host=HOST_NAME,
                user=USER_NAME,
                passwd=USER_PASSWORD,
                database=DB_NAME,
                port=PORT_NUMBER
            )
            print(f'"DATABASE CONNECTED"')
        except Error as err:
            raise SqlException(str(err))
        
    def refresh(self):
        initial_query = """SELECT song_id, refresh FROM Songs;"""
        refr_pairs = self.read_query(initial_query)
        print(refr_pairs)

        for pair in refr_pairs:
            if pair[1] is None or pair[1] < time.time()+CHECKING_INTERVAL:
                query2 = f"""SELECT Songs.song_name, Authors.author_name FROM Songs INNER JOIN Authors ON Songs.author_id=Authors.author_id WHERE song_id={pair[0]};"""
                retval2 = self.read_query(query2)[0]
                print(retval2)
                print(f"{retval2[0]} {retval2[1]}")
                search = YouTubeInfo.search_yt(f"{retval2[0]} {retval2[1]}")
                source = search[0]
                query3 = f"""UPDATE Songs SET song_link="{source}", refresh={time.time()+EXPIRY_TIME} WHERE song_id={pair[0]};"""
                self.execute_query(query3)
                print(f"Updated song_id {pair[0]}, next refresh on {time.time()+EXPIRY_TIME}")

    def execute_query(self, query: str) -> None:
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
        except Error as err:
            raise SqlException(str(err))

    def read_query(self, query: str):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
        except Error as err:
            raise SqlException(str(err))
        else:
            return result


if __name__ == '__main__':
    SR = SourceRefresher()
    while True:
        try:
            SR.refresh()
        except SqlException:
            pass
        time.sleep(LOOP_INTERVAL)
