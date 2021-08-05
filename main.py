# -*- coding: utf-8 -*-
import pyglet
from pyglet.window import key
from pyglet.gl import *
from collections import OrderedDict
import datetime
import psutil
from PIL import Image
from os import path
from scipy.interpolate import interp1d
import geopy.distance

class PipOS:

    def __init__(self):
        # TODO reduce instance variable count
        self.menu_names = [('SYSTEM', ['ABOUT', 'EXPANSION']),
                           ('STATUS', ['ENVIRONMENT']),
                           ('DATA', ['CHIPMAP', 'ARCHIVES'])]
        self.menu_names = OrderedDict(self.menu_names)  # The order matters for printing in the GUI
        self.font_name = 'monofonto'
        self.menu_label_text_size = 20
        self.tab_label_text_size = 16
        self.screen_label_text_size = 10
        self.info_bar_height = 24
        self.active_menu = 0
        self.active_tab = 0
        self.tab_offsets = []
        self.tab_offset = 0
        self.tab_info_labels = []
        self.volume = 50
        self.volume_max = 100
        self.env_temp = 0.0
        self.env_humid = 0.0
        self.env_CO2 = 0
        self.gps_lock = False
        self.gps_lon = -121.332
        self.gps_lat = 38.608
        self.target_lat_cardinal = 'N'
        self.target_lon_cardinal = 'W'
        self.target_lon = -121.33
        self.target_lat = 38.55
        self.target_distance = 0.0
        self.reticle_lon = -121.3125
        self.reticle_lat = 38.5625
        self.low_battery = False
        self.overbright_mode = False
        self.ui_colors = {'GREEN': (25, 255, 132, 255),
                          'AMBER': (215, 156, 41, 255),
                          'WHITE': (250, 250, 250, 255)}
        self.active_ui_color = 'WHITE'
        self.menu_sfx = pyglet.resource.media('ui_menu_mode.wav')
        self.tab_sfx = pyglet.resource.media('ui_menu_tab.wav')
        self.enter_sfx = pyglet.resource.media('ui_menu_ok.wav')
        self.close_sfx = pyglet.resource.media('ui_menu_cancel.wav')
        self.scroll_sfx = pyglet.resource.media('ui_pipboy_scroll.wav')
        self.datetime = '|'
        self.map_bounds = {'START_LAT': 38.500, 'END_LAT': 38.625, 'START_LON': -121.3750, 'END_LON': -121.250}
        self.map_image = pyglet.image.load('Map.png')
        self.map_image_list = []
        self.map_zoom_idx = 0
        self.zoom_locked = False
        self.item_selected = False  # Enable on a menu so scrolling and button behavior affects the settings
        self.map_focus_coords = [0, 0]
        self.visible_map_region = self.map_image.get_region(self.map_focus_coords[0], self.map_focus_coords[1], 320, 320)
        self.about_text = 'ChipOS v0.0.1 beta\n\n' \
                          'COPYRIGHT 2021 Squirrel Computers(R)\n' \
                          'LOADER V1.0\n' \
                          'EXEC VERSION 21.10'
        with open('us_constitution.txt', 'r') as self.raw_file:
            self.raw_text = self.raw_file.read()
        self.document = pyglet.text.document.FormattedDocument()
        self.document.insert_text(0, self.raw_text, attributes=dict(font_name='Monofonto',
                                                                    font_size=self.screen_label_text_size,
                                                                    color=self.ui_colors['GREEN']))
        self.layout = pyglet.text.layout.ScrollableTextLayout(self.document, width=300, height=240,
                                                              multiline=True)
        self.layout.view_y = 50

    def get_system_status(self):

        self.cpu_usage = psutil.cpu_percent(interval=0.1, percpu=True)
        self.system_memory = psutil.virtual_memory()
        return self.cpu_usage, self.system_memory

    def make_map_images(self):
        # Create a sequence of smaller images so that "zooming" is smooth and less loading is required
        full_image = Image.open('Map.png')

        for idx in range(1, 10):
            new_width = int(idx / 10 * full_image.width)
            new_height = int(idx / 10 * full_image.height)
            img = full_image.resize((new_width, new_height), Image.ANTIALIAS)
            img.save('Map' + str(idx) + '.png')

    def get_map_images(self):

        for idx in range(1, 10):
            self.map_image_list.append(pyglet.image.load('Map' + str(idx) + '.png'))
        print(self.map_image_list)

    def get_sensor_data(self):
        pass


pipboy = PipOS()

if not path.exists('Map1.png'):
    pipboy.make_map_images()
pipboy.get_map_images()
pipboy.map_image = pipboy.map_image_list[0]
window = pyglet.window.Window(width=320, height=480)
# window = pyglet.window.Window(width=320, height=480, fullscreen=True)


def main():

    # Although I don't want these hardcoded, it's a mess to make this more dynamic. This is fine for now
    menu_system = pyglet.text.Label('SYSTEM',
                                   font_name=pipboy.font_name,
                                   font_size=pipboy.menu_label_text_size,
                                   x=window.width // 2,
                                   y=window.height - pipboy.menu_label_text_size // 2,
                                   anchor_x='center', anchor_y='center',
                                   color=pipboy.ui_colors[pipboy.active_ui_color])

    menu_status = pyglet.text.Label('STATUS',
                                   font_name=pipboy.font_name,
                                   font_size=pipboy.menu_label_text_size,
                                   x=window.width // 2,
                                   y=window.height - pipboy.menu_label_text_size // 2,
                                   anchor_x='center', anchor_y='center',
                                   color=pipboy.ui_colors[pipboy.active_ui_color])

    menu_data = pyglet.text.Label('DATA',
                                   font_name=pipboy.font_name,
                                   font_size=pipboy.menu_label_text_size,
                                   x=window.width // 2,
                                   y=window.height - pipboy.menu_label_text_size // 2,
                                   anchor_x='center', anchor_y='center',
                                   color=pipboy.ui_colors[pipboy.active_ui_color])

    # Dynamically align the labels so they're evenly spaced from center
    # Do this after assignment so we can reference the content_width of the objects
    menu_system.x = menu_system.x - menu_system.content_width // 2 - menu_status.content_width // 2 - 16
    menu_data.x = menu_data.x + menu_data.content_width // 2 + menu_status.content_width // 2 + 16

    menu_labels = [menu_system, menu_status, menu_data]  # Allow selecting

    active_tab_label = pyglet.text.Label(pipboy.menu_names[menu_labels[pipboy.active_menu].text][pipboy.active_tab],
                                   font_name=pipboy.font_name,
                                   font_size=pipboy.tab_label_text_size,
                                   x=window.width // 2,
                                   y=window.height // 2,
                                   anchor_x='center', anchor_y='center',
                                   color=pipboy.ui_colors[pipboy.active_ui_color])

    tab_labels = pyglet.text.Label(' '.join(pipboy.menu_names[menu_labels[pipboy.active_menu].text]),
                                   font_name=pipboy.font_name,
                                   font_size=pipboy.tab_label_text_size,
                                   x=window.width // 2,
                                   y=window.height - (pipboy.tab_label_text_size*3),
                                   anchor_x='center', anchor_y='center',
                                   color=pipboy.ui_colors[pipboy.active_ui_color])

    clock_label = pyglet.text.Label(pipboy.datetime,
                                   font_name=pipboy.font_name,
                                   font_size=pipboy.menu_label_text_size,
                                   x=window.width // 2,
                                   y=pipboy.info_bar_height // 2 + 1,
                                   anchor_x='center', anchor_y='center',
                                   color=pipboy.ui_colors[pipboy.active_ui_color])

    info_label_0 = pyglet.text.Label(pipboy.about_text,
                                   font_name=pipboy.font_name,
                                   font_size=pipboy.screen_label_text_size,
                                   x=window.width // 2,
                                   y=window.height // 2,
                                   anchor_x='center', anchor_y='center',
                                   color=pipboy.ui_colors[pipboy.active_ui_color],
                                   width=320,
                                   multiline=True)

    info_label_1 = pyglet.text.Label('UNKOWN',
                                   font_name=pipboy.font_name,
                                   font_size=pipboy.screen_label_text_size,
                                   x=window.width // 2,
                                   y=40,
                                   anchor_x='center', anchor_y='center',
                                   color=pipboy.ui_colors[pipboy.active_ui_color])

    # TODO: Setups should be in separate files
    def setup_tab_about():
        # Show fake operating system data mixed in with real memory stats
        pipboy.get_system_status()
        memory_string = '\nMEM AVAIL:{}GB\nMEM USED:{}GB'.format(pipboy.system_memory.available//1000000000,
                                                                 pipboy.system_memory.used//1000000000)
        info_label_0.x = window.width // 2
        info_label_0.y = window.height // 2 + 80
        info_label_0.font_size = pipboy.screen_label_text_size
        info_label_0.width = 240
        info_label_0.multiline = True
        info_label_0.text = pipboy.about_text + memory_string

        pipboy.tab_info_labels.append(info_label_0)

    def setup_tab_audio(symbol):

        if symbol == key.SPACE:  # TODO: update this so that each tab has a selectable attribute instead of this code
            pipboy.item_selected = True

        if pipboy.item_selected:
            if symbol == key.UP:
                pipboy.volume += 1
            elif symbol == key.DOWN:
                pipboy.volume -= 1

        pipboy.volume = constrain(pipboy.volume, 0, pipboy.volume_max)

        # TODO: This doesn't update right? Find the source
        pyglet.media.Player.volume = float(pipboy.volume / 100.0)

        info_label_0.x = window.width // 2
        info_label_0.y = window.height // 2
        info_label_0.font_size = pipboy.tab_label_text_size
        info_label_0.multiline = False
        info_label_0.width = 0
        info_label_0.text = 'VOLUME: {}%'.format(pipboy.volume)

        pipboy.tab_info_labels.append(info_label_0)

    def setup_tab_expansion():

        info_label_0.x = window.width // 2
        info_label_0.y = window.height // 2
        info_label_0.font_size = pipboy.tab_label_text_size
        info_label_0.multiline = False
        info_label_0.width = 0
        info_label_0.text = 'LOAD EXPANSION MODULE'

        pipboy.tab_info_labels.append(info_label_0)

    def setup_tab_user():

        info_label_0.x = window.width // 2
        info_label_0.y = window.height // 2
        info_label_0.font_size = pipboy.tab_label_text_size
        info_label_0.multiline = False
        info_label_0.width = 0
        info_label_0.text = 'BIOMETRICS UNAVAILABLE'

        pipboy.tab_info_labels.append(info_label_0)

    def setup_tab_environment():
        # Show sensor data
        # TODO: Get sensor data...
        info_label_0.x = 180
        info_label_0.y = window.height // 2
        info_label_0.font_size = pipboy.tab_label_text_size
        info_label_0.width = 320
        info_label_0.multiline = True
        info_label_0.text = 'TEMPERATURE: {0:1f}°F\nHUMIDITY: {1:1f}\nCO2: {2}PPM'.format(pipboy.env_temp,
                                                                                         pipboy.env_humid,
                                                                                         pipboy.env_CO2)
        pipboy.tab_info_labels.append(info_label_0)

    def setup_tab_map(symbol):

        if pipboy.item_selected:
            if symbol in (key.UP, key.DOWN, key.LEFT, key.RIGHT):

                if symbol == key.UP:
                    pipboy.reticle_lat += .0025
                elif symbol == key.DOWN:
                    pipboy.reticle_lat -= .0025
                elif symbol == key.RIGHT:
                    pipboy.reticle_lon += .0025
                    pipboy.scroll_sfx.play()
                elif symbol == key.LEFT:
                    pipboy.reticle_lon -= .0025
                    pipboy.scroll_sfx.play()

            # print('Map Selected:{}'.format(pipboy.item_selected))
            if symbol == key.SPACE:

                # Update the current target coordinates and map marker
                pipboy.target_lat = pipboy.reticle_lat
                pipboy.target_lon = pipboy.reticle_lon
                pipboy.target_distance = geopy.distance.distance((pipboy.gps_lat, pipboy.gps_lon),
                                                                    (pipboy.target_lat, pipboy.target_lon)).mi

                if pipboy.target_lat > 0:
                    pipboy.target_lat_cardinal = 'N'
                else:
                    pipboy.target_lat_cardinal = 'S'
                if pipboy.target_lon > 0:
                    pipboy.target_lon_cardinal = 'E'
                else:
                    pipboy.target_lon_cardinal = 'W'

        if symbol == key.SPACE:
            pipboy.item_selected = True
        elif symbol == key.NUM_4:
            pipboy.item_selected = False

        info_label_0.x = window.width // 2
        info_label_0.y = 40
        info_label_0.font_size = pipboy.screen_label_text_size
        info_label_0.multiline = False
        info_label_0.width = 0
        info_label_0.text = 'DISTANCE: {0:.2f}mi'.format(pipboy.target_distance)

        info_label_1.x = window.width // 2
        info_label_1.y = 400
        info_label_1.font_size = pipboy.screen_label_text_size
        info_label_1.text = 'TARGET: {0:.3f}{2}, {1:.3f}{3}'.format(abs(pipboy.target_lat), abs(pipboy.target_lon),
                                                                    pipboy.target_lat_cardinal,
                                                                    pipboy.target_lon_cardinal)

        pipboy.visible_map_region = get_map_focus(pipboy.map_focus_coords[0], pipboy.map_focus_coords[1])
        pipboy.tab_info_labels.append(info_label_0)
        pipboy.tab_info_labels.append(info_label_1)

    def setup_tab_archives(symbol):

        pipboy.layout.x, pipboy.layout.y = 10, window.height * 3/4
        pipboy.layout.anchor_x = 'left'
        pipboy.layout.anchor_y = 'top'
        if pipboy.item_selected:
            if symbol == key.UP:
                pipboy.layout.view_y -= pipboy.screen_label_text_size + 2
            elif symbol == key.DOWN:
                pipboy.layout.view_y += pipboy.screen_label_text_size + 2

        if symbol == key.SPACE:
            pipboy.item_selected = True

    def get_time(pip_now):

        pip_now = datetime.datetime.now()
        pipboy.datetime = pip_now.strftime('%H:%M | %m.%d.%Y')
        clock_label.text = pipboy.datetime

    pyglet.clock.schedule_interval(get_time, 1)

    def get_tab_offsets():
        # Find the width of the current tab words so we can place the underline properly
        pipboy.tab_offsets.clear()
        for idx, tabs in enumerate(pipboy.menu_names[menu_labels[pipboy.active_menu].text]):
            active_tab_label.text = pipboy.menu_names[menu_labels[pipboy.active_menu].text][idx]
            pipboy.tab_offsets.append(active_tab_label.content_width)
        pipboy.tab_offset = 0
        for idx in range(pipboy.active_tab):
            pipboy.tab_offset += (idx * 11) + pipboy.tab_offsets[
                idx]  # TODO get rid of magic number eleven (this is the character width at the current font size)
        if pipboy.active_tab > 0:
            pipboy.tab_offset += 11  # #TODO get rid of this manual offset, but needed for now
        active_tab_label.text = pipboy.menu_names[menu_labels[pipboy.active_menu].text][pipboy.active_tab]
        # print(pipboy.tab_offset)
        print(pipboy.menu_names[menu_labels[pipboy.active_menu].text])
        # pipboy.get_system_status()
        # print('CPU: {}, MEM AVAIL: {}, MEM USED:{}'.format(pipboy.cpu_usage, pipboy.system_memory.available, pipboy.system_memory.used))

    def get_map_focus(x, y):
        # Choose the window within the larger map image of where we're looking
        map_focus_region = pipboy.map_image.get_region(x, y, 320, 320)
        return map_focus_region

    def check_map_focus():
        # Keep the map zoom window in visible boundaries
        if pipboy.map_focus_coords[0] > pipboy.map_image.width - 320:
                pipboy.map_focus_coords[0] = pipboy.map_image.width - 320
        if pipboy.map_focus_coords[0] < 0:
            pipboy.map_focus_coords[0] = 0
        if pipboy.map_focus_coords[1] > pipboy.map_image.height - 320:
            pipboy.map_focus_coords[1] = pipboy.map_image.height - 320
        if pipboy.map_focus_coords[1] < 0:
            pipboy.map_focus_coords[1] = 0

    @window.event
    def on_key_press(symbol, modifier):

        # Remove the info from previous tabs before adding the current tab info to draw
        pipboy.tab_info_labels.clear()

        # Select the active Menu
        if symbol in (key.NUM_1, key.NUM_2, key.NUM_3):
            if symbol == key.NUM_1:
                pipboy.active_menu = 0  # 'SYSTEM' it's more useful for active_menu to be an integer than a string for now
            elif symbol == key.NUM_2:
                pipboy.active_menu = 1  # 'STATUS'
            elif symbol == key.NUM_3:
                pipboy.active_menu = 2  # 'DATA'
            pipboy.menu_sfx.play()
            pipboy.active_tab = 0

        elif symbol == key.NUM_4:
            # Deselect active tab to re-enable moving to a new tab
            pipboy.item_selected = False
            # Flash this menu LED
            pipboy.close_sfx.play()
            print('CLOSE')
        elif symbol == key.SPACE:
            pipboy.enter_sfx.play()  # TODO make so it only plays on tab that is selectable

        # Select the active Tab
        if pipboy.item_selected == False:
            if symbol == key.RIGHT:  # Change to be any tab is selected
                pipboy.tab_sfx.play()
                pipboy.active_tab += 1
                if pipboy.active_tab >= len(pipboy.menu_names[menu_labels[pipboy.active_menu].text]):
                    pipboy.active_tab = 0
            elif symbol == key.LEFT:
                pipboy.tab_sfx.play()
                pipboy.active_tab -= 1
                if pipboy.active_tab < 0:
                    pipboy.active_tab = len(pipboy.menu_names[menu_labels[pipboy.active_menu].text]) - 1

        if symbol in (key.UP, key.DOWN):
            pipboy.scroll_sfx.play()

        # This is basically a switch case, but needs to be better
        if pipboy.active_menu == 0:  # SYSTEM
            # light up this menu LED
            if pipboy.active_tab == 0:  # ABOUT
                setup_tab_about()
            elif pipboy.active_tab == 1:  # AUDIO
                setup_tab_audio(symbol)
            elif pipboy.active_tab == 2:  # EXPANSION
                setup_tab_expansion()

        if pipboy.active_menu == 1:  # STATUS
            # light up this menu LED
            if pipboy.active_tab == 0:  # USER
                setup_tab_user()
            elif pipboy.active_tab == 1:  # ENVIRONMENT
                setup_tab_environment()

        if pipboy.active_menu == 2:  # DATA
            # light up this menu LED
            if pipboy.active_tab == 0:  # MAP
                setup_tab_map(symbol)
            elif pipboy.active_tab == 1:  # ARCHIVES
                setup_tab_archives(symbol)

        elif symbol == key.PAGEUP:
            # TODO Figure out how to zoom centered on the reticle
            # Zooming is not functional right now
            pipboy.map_zoom_idx += 1
            if pipboy.map_zoom_idx >= len(pipboy.map_image_list):
                pipboy.map_zoom_idx = len(pipboy.map_image_list) - 1
            pipboy.map_image = pipboy.map_image_list[pipboy.map_zoom_idx]
            #ratio = pipboy.map_image.width / pipboy.map_image_list[pipboy.map_zoom_idx-1].width
            #print('RatioX: {}'.format(ratio_x))
            #ratio_y = pipboy.map_image.height / pipboy.map_image_list[pipboy.map_zoom_idx-1].height
            if pipboy.map_zoom_idx != len(pipboy.map_image_list) - 1:
                print('Zoom!')
            pipboy.map_focus_coords[0] = int(pipboy.map_image.width / 2 - 160)
            pipboy.map_focus_coords[1] = int(pipboy.map_image.height / 2 - 160)
            pipboy.scroll_sfx.play()

        elif symbol == key.PAGEDOWN:
            pipboy.zoom_locked = False
            pipboy.map_zoom_idx -= 1
            if pipboy.map_zoom_idx < 0:
                pipboy.map_zoom_idx = 0
            pipboy.map_image = pipboy.map_image_list[pipboy.map_zoom_idx]
            pipboy.map_focus_coords[0] = int(pipboy.map_image.width / 2 - 160)
            pipboy.map_focus_coords[1] = int(pipboy.map_image.height / 2 - 160)
            pipboy.scroll_sfx.play()

        get_tab_offsets()
        #check_map_focus()
        #print('Zoom:{}'.format(pipboy.map_zoom_idx))
        #print('Focused at ({}, {})\n'.format(pipboy.map_focus_coords[0], pipboy.map_focus_coords[1]))
        #pipboy.visible_map_region = get_map_focus(pipboy.map_focus_coords[0], pipboy.map_focus_coords[1])
        tab_labels.text = ' '.join(pipboy.menu_names[menu_labels[pipboy.active_menu].text])

    def draw_info_bar():
        # OpenGL requires float values of 0 to 1 for colors, so we need to convert it first
        # or else we'd have to specify a color for each index, which is gross and redundant for solid fills
        r, g, b, a = (float(color) / 255.0 * .5 for color in pipboy.ui_colors[pipboy.active_ui_color])
        glColor4f(r, g, b, a)
        pyglet.graphics.draw(4, pyglet.gl.GL_POLYGON,
                             ('v2i', (0, 0,
                                      0, pipboy.info_bar_height,
                                      window.width, pipboy.info_bar_height,
                                      window.width, 0)))

    def draw_menu_lines():
        # This ui element is "full brightness", so we have to reset the color
        r, g, b, a = (float(color) / 255.0 for color in pipboy.ui_colors[pipboy.active_ui_color])
        glColor4f(r, g, b, a)
        glLineWidth(4)
        # Pyglet mentions a background color for text, but it doesn't seem to work, so this is drawn as two separate strips
        glBegin(GL_LINE_STRIP)
        glVertex2i(2, menu_labels[pipboy.active_menu].y - pipboy.menu_label_text_size - 4)
        glVertex2i(2, menu_labels[pipboy.active_menu].y - pipboy.menu_label_text_size)
        glVertex2i(menu_labels[pipboy.active_menu].x - menu_labels[pipboy.active_menu].content_width // 2 - 8, menu_labels[pipboy.active_menu].y - pipboy.menu_label_text_size)
        glVertex2i(menu_labels[pipboy.active_menu].x - menu_labels[pipboy.active_menu].content_width // 2 - 8, menu_labels[pipboy.active_menu].y)
        glVertex2i(menu_labels[pipboy.active_menu].x - menu_labels[pipboy.active_menu].content_width // 2 - 4, menu_labels[pipboy.active_menu].y)
        glEnd()
        glBegin(GL_LINE_STRIP)
        glVertex2i(menu_labels[pipboy.active_menu].x + menu_labels[pipboy.active_menu].content_width // 2 + 4, menu_labels[pipboy.active_menu].y)
        glVertex2i(menu_labels[pipboy.active_menu].x + menu_labels[pipboy.active_menu].content_width // 2 + 8, menu_labels[pipboy.active_menu].y)
        glVertex2i(menu_labels[pipboy.active_menu].x + menu_labels[pipboy.active_menu].content_width // 2 + 8, menu_labels[pipboy.active_menu].y - pipboy.menu_label_text_size)
        glVertex2i(window.width - 2, menu_labels[pipboy.active_menu].y - pipboy.menu_label_text_size)
        glVertex2i(window.width - 2, menu_labels[pipboy.active_menu].y - pipboy.menu_label_text_size - 4)
        glEnd()
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
                             ('v2i', (tab_labels.x - tab_labels.content_width // 2 + pipboy.tab_offset,
                                      tab_labels.y - pipboy.tab_label_text_size // 2 - 4,
                                      tab_labels.x - tab_labels.content_width // 2 + pipboy.tab_offset + active_tab_label.content_width,
                                      tab_labels.y - pipboy.tab_label_text_size // 2 - 4)))

    def draw_map_lines():

        # Draw border lines above and below the map area
        glBegin(GL_LINE_STRIP)
        glVertex2i(1, 380)
        glVertex2i(1, 384)
        glVertex2i(window.width-1, 384)
        glVertex2i(window.width-1, 380)
        glEnd()
        glBegin(GL_LINE_STRIP)
        glVertex2i(1, 60)
        glVertex2i(1, 56)
        glVertex2i(window.width-1, 56)
        glVertex2i(window.width-1, 60)
        glEnd()

    def constrain(value, min, max):

        if value > max:
            value = max
        if value < min:
            value = min

        return value

    def get_pixel_location_from_coordinates(lon, lat):
        # First, transform coordinates from lat/lon to pixel location
        # These scaling factors were manually calculated elsewhere
        # since the actual map is a rectangle within the full image
        #  also scale according to zoom
        x_left = int(.14 * pipboy.map_image.width)
        y_bottom = int(.143 * pipboy.map_image.height) + 60
        x_right = int(.862 * pipboy.map_image.width)
        y_top = int(.903 * pipboy.map_image.height) + 60
        lon = constrain(lon, pipboy.map_bounds['START_LON'], pipboy.map_bounds['END_LON'])
        lat = constrain(lat, pipboy.map_bounds['START_LAT'], pipboy.map_bounds['END_LAT'])
        transform_lon = interp1d([pipboy.map_bounds['START_LON'], pipboy.map_bounds['END_LON']], [x_left, x_right])
        transform_lat = interp1d([pipboy.map_bounds['START_LAT'], pipboy.map_bounds['END_LAT']], [y_bottom, y_top])
        x_pixel = int(transform_lon(lon))
        y_pixel = int(transform_lat(lat))
        x_pixel = constrain(x_pixel, 0, 320)
        y_pixel = constrain(y_pixel, 0, 320 + 60)
        return x_pixel, y_pixel

    def draw_current_location(lon, lat):

        x, y = get_pixel_location_from_coordinates(lon, lat)
        glPointSize(8)
        pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
                             ('v2i', (x, y)),
                             ('c4B', pipboy.ui_colors[pipboy.active_ui_color]))
        glPointSize(4)

    def draw_reticle(lon, lat):

        lon = constrain(lon, pipboy.map_bounds['START_LON'], pipboy.map_bounds['END_LON'])
        lat = constrain(lat, pipboy.map_bounds['START_LAT'], pipboy.map_bounds['END_LAT'])
        x, y = get_pixel_location_from_coordinates(lon, lat)
        glPointSize(6)

        # Reticle dot
        pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
                             ('v2i', (x, y)),
                             ('c4B', pipboy.ui_colors[pipboy.active_ui_color])
                             )
        # Reticle brackets
        glBegin(GL_LINE_STRIP)
        glVertex2i(x - 6, y + 12)
        glVertex2i(x - 12, y + 12)
        glVertex2i(x - 12, y - 12)
        glVertex2i(x - 6, y - 12)
        glEnd()
        glBegin(GL_LINE_STRIP)
        glVertex2i(x + 6, y + 12)
        glVertex2i(x + 12, y + 12)
        glVertex2i(x + 12, y - 12)
        glVertex2i(x + 6, y - 12)
        glEnd()

    def draw_map_marker(lon, lat):

        x, y = get_pixel_location_from_coordinates(lon, lat)
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
                             ('v2i', (x, y, x, y+12)))

        # Draw the box above the marker line
        pyglet.graphics.draw(4, pyglet.gl.GL_POLYGON,
                             ('v2i', (x-6, y+12,
                                      x-6, y+24,
                                      x+6, y+24,
                                      x+6, y+12)))

        # Draw the line from the user to the marker coordinates
        user_x, user_y = get_pixel_location_from_coordinates(pipboy.gps_lon, pipboy.gps_lat)
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(1, 0x00FF)
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
                             ('v2i', (user_x, user_y, x, y)))
        glDisable(GL_LINE_STIPPLE)

    @window.event
    def on_draw():

        # Start with a clean slate
        window.clear()
        pyglet.clock.tick()

        # Draw persistent info like the Menu/Tab text up top and clock bar
        draw_info_bar()
        clock_label.draw()
        draw_menu_lines()
        for label in menu_labels:
            label.draw()
        tab_labels.draw()

        # Draw the relevant textual information found on the active Tab
        for label in pipboy.tab_info_labels:
            label.draw()

        if pipboy.item_selected:
            draw_map_lines()

        # Draw the graphical elements (if any) for the active Tab
        if pipboy.active_menu == 0:  # SYSTEM

            if pipboy.active_tab == 0:  # ABOUT
                pass
            elif pipboy.active_tab == 1:  # AUDIO
                pass
            elif pipboy.active_tab == 2:  # EXPANSION
                pass

        if pipboy.active_menu == 1:  # STATUS

            if pipboy.active_tab == 0:  # USER
                pass
            elif pipboy.active_tab == 1:  # ENVIRONMENT
                pass

        if pipboy.active_menu == 2:  # DATA

            if pipboy.active_tab == 0:  # MAP
                pipboy.visible_map_region.blit(0, 60)
                draw_map_marker(pipboy.target_lon, pipboy.target_lat)
                draw_current_location(pipboy.gps_lon, pipboy.gps_lat)
                draw_reticle(pipboy.reticle_lon, pipboy.reticle_lat)
            elif pipboy.active_tab == 1:  # ARCHIVES
                pipboy.layout.draw()

    pyglet.app.run()


if __name__ == '__main__':

    main()
