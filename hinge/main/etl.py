import pandas as pd
from pandas import DataFrame
import sqlite3


class Etl:
    @staticmethod
    def extract(file_path: str, delimiter: str) -> DataFrame:
        df = pd.read_csv(file_path, delimiter=delimiter)
        return df

    def column_rename(self, df: DataFrame, columns: dict) -> DataFrame:
        df = df.rename(columns=columns)
        return df

    def name_transformation(self, df: DataFrame, column) -> DataFrame:
        df[['first_name', 'last_name']] = df[column].str.split(n=1, expand=True)
        df = df.drop(column, axis=1)
        return df

    def date_transform(self, df: DataFrame, column, from_format, to_format) -> DataFrame:
        df[column] = pd.to_datetime(df[column], format=from_format)
        df[column] = df[column].dt.strftime(to_format)
        return df

    def send_to_error(self, df: DataFrame, error_file_path) -> None:
        df['col_year'] = pd.to_datetime(df['dob']).dt.year

        # Filter records based on the condition (Member_since year is lesser than DOB)
        filtered_df = df[df['member_since'] > df['col_year']]
        error_df = df[df['member_since'] < df['col_year']]
        error_df.to_csv(error_file_path)
        return filtered_df.drop('col_year', axis=1)

    def load_to_db(self, df: DataFrame) -> None:
        # TODO connection to be received from secrets
        conn = sqlite3.connect('hinge.db')
        df.to_sql(df, conn, index=True, if_exists='append')


if __name__ == '__main__':
    etl = Etl()

    # TODO : Need to pass from the config parameters
    # Extractions
    us_golf_df = etl.extract('/Users/karthikeyanchandrasekar/Desktop/hinge/resources/unity_golf_club.csv',
                             delimiter=',')
    us_soft_df = etl.extract('/Users/karthikeyanchandrasekar/Desktop/hinge/resources/us_softball_league.tsv',
                             delimiter='\t')

    # column renaming
    # TODO : We can take this from file-mapping as global (config) file
    column_rename_mapping = {"joined_league": "member_since", "date_of_birth": "dob", "us_state": "state"}
    us_soft_df = etl.column_rename(us_soft_df, columns=column_rename_mapping)

    # Data Tranformation
    us_soft_df = etl.date_transform(us_soft_df, column='dob', from_format='%m/%d/%Y', to_format='%Y/%m/%d')

    # name tranformation
    us_soft_df = etl.name_transformation(us_soft_df, column='name')

    # Merge transactions
    # TODO : We have two letter state code in golf transactions,however complete name in soft ball transaction, need to standardize using a global reference table
    players_transactions = pd.concat([us_soft_df, us_golf_df], ignore_index=True)

    # Error record extraction &  valid transactions
    # TODO : We can include current_date paraemeter for folders and store the error record

    master_set = etl.send_to_error(players_transactions,
                                   error_file_path='/Users/karthikeyanchandrasekar/Desktop/hinge/error_records/error_file.csv')

    # load into sql lite

    etl.load_to_db(master_set)
