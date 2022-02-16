import plotly.graph_objects as go
from config import MapBox, TempDirectory
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import dash_loading_spinners as dls
from dash.dependencies import Input, Output, State
from vkfinder import VKFinder
from geo_point import GeoPoint
import pandas as pd
import os
from datetime import datetime


class GeoVisualizer:
    def __init__(self):
        self.app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.mapbox_token = MapBox.token
        self.create_layout()
        self.app.callback([Output('photo', 'src'), Output('photo_link', 'href'),
                           Output('photo_description', 'children'), Output('photo_date', 'children')],
                          Input('map', 'clickData'))(self.get_image_callback)
        self.app.callback([Output('map', 'figure'), Output('div_modal', 'children')],
                          Input('submit_id', 'n_clicks'),
                          State('profile_id', 'value'))(self.set_geopoints_callback)
        self.df = pd.DataFrame()
        self.vk = VKFinder()

    def create_map(self, lats: list, longs: list):
        if not lats:
            lats = [0.00]
        if not longs:
            longs = [0.00]
        center_lat = (max(lats) + min(lats)) / 2.0
        center_long = (max(longs) + min(longs)) / 2.0

        data = go.Scattermapbox(
            lat=lats,
            lon=longs,
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=14)
        )
        layout = dict(
            hovermode='closest',
            height=1000,
            mapbox=dict(
                accesstoken=self.mapbox_token,
                bearing=0,
                style='open-street-map',
                center=go.layout.mapbox.Center(
                    lat=center_lat,
                    lon=center_long),
                pitch=0,
                zoom=10)
        )
        return go.Figure(data=data, layout=layout)

    def create_modal(self, header: str, message: str, is_open=True):
        return dbc.Modal([dbc.ModalHeader(dbc.ModalTitle(header)),
                          dbc.ModalBody(message)],
                         id='modal',
                         is_open=is_open)

    def create_layout(self):
        self.app.layout = html.Div(
            children=[
                html.Div(id='div_modal'),
                html.Div(children=[
                    html.Div([dcc.Input(id='profile_id',
                                        placeholder='Profile ID',
                                        type='text'),
                              html.Button('Submit', id='submit_id'),
                              html.Div([], id='spinner_div')],
                             style={'display': 'inline-block'}),
                    dls.Hash(
                        dcc.Graph(id='map'),
                        color="#435278",
                        speed_multiplier=2,
                        size=100
                    )],
                    style={'width': '80%'}
                ),
                html.Div(children=[
                    html.H1('Photo'),
                    html.A(children=[
                        html.Img(id='photo',
                                 style={'width': '100%'})],
                           id='photo_link',
                           target='_blank'),
                    html.H5('Created At'),
                    html.H6(id='photo_date'),
                    html.H5('Description'),
                    html.H6(id='photo_description')
                ],
                    style={'width': '20%'})
            ],
            style={'display': 'flex', 'flex-direction': 'row', 'height': '100%'}
        )

    def get_image_callback(self, click_data: dict):
        if click_data:
            if len(click_data.get('points')):
                index = click_data.get('points')[0].get('pointNumber')
                url = self.df.source.tolist()[index]
                profile_link = self.df.profile_link.tolist()[index]
                photo_description = self.df.description.tolist()[index]
                photo_date = self.df.created.tolist()[index]
                return url, profile_link, photo_description, photo_date
        return '', '', '', ''

    def set_geopoints_callback(self, n_clicks: int, value: str):
        try:
            if os.path.exists(f'{TempDirectory.tmp_dir}{value}_geo.csv'):
                self.df = pd.read_csv(f'{TempDirectory.tmp_dir}{value}_geo.csv')
            else:
                self.get_geos_from_profile(value)
            if not len(self.df.index):
                return self.create_map([], []), self.create_modal('Геолокаций не найдено', 'Ни на одной фотографии пользователя нет геолокации')
            lats = self.df.lat.to_list()
            longs = self.df.long.to_list()
            fig = self.create_map(lats, longs)
            return fig, None
        except Exception as e:
            if n_clicks:
                return self.create_map([], []), self.create_modal('Геолокаций не найдено', 'Ни на одной фотографии пользователя нет геолокации')
            else:
                return self.create_map([], []), None

    def get_geos_from_profile(self, profile_id: str):
        try:
            photos = self.vk.get_profile_photos(profile_id)
            full_photos = self.vk.get_photos_by_id([f'{i.get("owner_id")}_{i.get("id")}' for i in photos if i.get('lat')])
            profile_link_pattern = 'https://vk.com/albums%s?z=photo%s_%s'
            geo_points = []
            for photo in full_photos:
                lat = photo.get('lat')
                long = photo.get('long')
                photo_source_url = photo.get('url')
                photo_in_profile_link = profile_link_pattern % (photo.get('owner_id'), photo.get('owner_id'), photo.get('id'))
                photo_desc = photo.get('text')
                photo_created_at = datetime.utcfromtimestamp(photo.get('date')).strftime('%Y-%m-%d %H:%M:%S')
                geo_points.append(GeoPoint(lat, long, photo_source_url, photo_in_profile_link, photo_desc, photo_created_at))
            self.df = pd.DataFrame([i.to_dict() for i in geo_points])
            self.df.to_csv(f'{TempDirectory.tmp_dir}{profile_id}_geo.csv', index=False)
        except Exception as e:
            pass

    def run(self):
        self.app.run_server(debug=True)


if __name__ == '__main__':
    app = GeoVisualizer()
    app.run()
