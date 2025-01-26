#!/usr/bin/env python3
import gi
import psutil
import datetime
import subprocess
import re
from datetime import datetime

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, GLib, Gdk, Gio

# В GTK4 ориентация задается через Gtk.Orientation
VERTICAL = Gtk.Orientation.VERTICAL
HORIZONTAL = Gtk.Orientation.HORIZONTAL


class SystemMonitorWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Настройка окна
        self.set_title("System Monitor")
        self.set_default_size(400, 600)
        
        # CSS стили
        css_provider = Gtk.CssProvider()
        css = """
            * {
                font-family: "MartianMono NFM Cond Med";
            }
            .monitor-window { 
                background-color: #1d2021;
                border-radius: 12px;
            }
            .widget-box {
                background-color: #282828;
                border-radius: 8px;
                padding: 12px;
                margin: 6px;
            }
            .section-label { 
                color: #ebdbb2;
                font-size: 18px;
                margin: 4px;
                font-weight: bold;
            }
            .info-box {
                background-color: #3c3836;
                border-radius: 6px;
                padding: 8px;
                margin: 4px;
            }
            .time-label {
                color: #fabd2f;
                font-size: 42px;
                font-weight: bold;
                margin: 4px;
            }
            .date-label {
                color: #fe8019;
                font-size: 18px;
                margin-bottom: 8px;
            }
            button {
                background-color: #504945;
                color: #ebdbb2;
                border-radius: 6px;
                padding: 8px 16px;
                margin: 4px;
                border: none;
            }
            button:hover {
                background-color: #665c54;
            }
            scale {
                margin: 8px 4px;
            }
            scale trough {
                background-color: #3c3836;
                border-radius: 6px;
                min-height: 6px;
            }
            scale highlight {
                background-color: #fabd2f;
                border-radius: 6px;
            }
            scale slider {
                background-color: #fe8019;
                border-radius: 50%;
                min-height: 16px;
                min-width: 16px;
            }
            .usage-bar {
                background-color: #3c3836;
                border-radius: 4px;
                min-height: 8px;
            }

            .network-speed-label {
                color: #83a598;
                font-size: 14px;
                margin: 4px;
            }

            .usage-bar progress {
                background-color: #b8bb26;
                border-radius: 4px;
            }
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Основной контейнер
        main_box = Gtk.Box(orientation=VERTICAL, spacing=8)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        main_box.add_css_class("monitor-window")
        self.set_child(main_box)

        # Время и дата
        time_box = Gtk.Box(orientation=VERTICAL, spacing=0)
        time_box.add_css_class("widget-box")
        self.time_label = Gtk.Label()
        self.time_label.add_css_class("time-label")
        self.date_label = Gtk.Label()
        self.date_label.add_css_class("date-label")
        time_box.append(self.time_label)
        time_box.append(self.date_label)
        main_box.append(time_box)

        # Системные ресурсы
        resources_box = Gtk.Box(orientation=VERTICAL, spacing=6)
        resources_box.add_css_class("widget-box")
        
        # CPU
        cpu_box = Gtk.Box(orientation=VERTICAL, spacing=4)
        cpu_box.add_css_class("info-box")
        cpu_label = Gtk.Label(label="Процессор")
        cpu_label.add_css_class("section-label")
        self.cpu_bar = Gtk.ProgressBar()
        self.cpu_bar.add_css_class("usage-bar")
        cpu_box.append(cpu_label)
        cpu_box.append(self.cpu_bar)
        resources_box.append(cpu_box)
        
        # RAM
        ram_box = Gtk.Box(orientation=VERTICAL, spacing=4)
        ram_box.add_css_class("info-box")
        ram_label = Gtk.Label(label="Память")
        ram_label.add_css_class("section-label")
        self.ram_bar = Gtk.ProgressBar()
        self.ram_bar.add_css_class("usage-bar")
        ram_box.append(ram_label)
        ram_box.append(self.ram_bar)
        resources_box.append(ram_box)
        
        main_box.append(resources_box)

        # Сеть
        network_box = Gtk.Box(orientation=VERTICAL, spacing=4)
        network_box.add_css_class("info-box")
        network_label = Gtk.Label(label="Скорость сети")
        network_label.add_css_class("section-label")
        self.network_bar = Gtk.ProgressBar()
        self.network_bar.add_css_class("usage-bar")
        self.network_speed_label = Gtk.Label()
        self.network_speed_label.add_css_class("network-speed-label")
        network_box.append(network_label)
        network_box.append(self.network_bar)
        network_box.append(self.network_speed_label)
        resources_box.append(network_box)

        # Управление
        controls_box = Gtk.Box(orientation=VERTICAL, spacing=8)
        controls_box.add_css_class("widget-box")

        # Громкость
        volume_box = Gtk.Box(orientation=VERTICAL, spacing=4)
        volume_label = Gtk.Label(label="Громкость")
        volume_label.add_css_class("section-label")
        self.volume_scale = Gtk.Scale(orientation=HORIZONTAL)
        self.volume_scale.set_range(0, 100)
        self.init_volume_scale(self.volume_scale)
        self.volume_scale.connect('value-changed', self.on_volume_changed)
        volume_box.append(volume_label)
        volume_box.append(self.volume_scale)
        controls_box.append(volume_box)
        
 
# Основной контейнер для музыкального блока (вертикальная ориентация)
        music_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        music_box.add_css_class("widget-box")

# Контейнер для кнопок (горизонтальная ориентация)
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        prev_button = Gtk.Button(label="󰼨")
        play_pause_button = Gtk.Button(label="󰏥")
        next_button = Gtk.Button(label="󰼧")

# Расширение кнопок для равномерного размещения
        prev_button.set_hexpand(True)
        play_pause_button.set_hexpand(True)
        next_button.set_hexpand(True)

# Подключение обработчиков событий
        prev_button.connect('clicked', lambda x: self.music_control('previous'))
        play_pause_button.connect('clicked', lambda x: self.music_control('play-pause'))
        next_button.connect('clicked', lambda x: self.music_control('next'))

# Добавляем кнопки в горизонтальный контейнер
        button_box.append(prev_button)
        button_box.append(play_pause_button)
        button_box.append(next_button)

# Метка для отображения текущего трека
        self.track_label = Gtk.Label(label="Музыка не играет")
        self.track_label.set_halign(Gtk.Align.CENTER)
        self.track_label.add_css_class("network-speed-label")

# Добавляем контейнер с кнопками и метку в вертикальный контейнер
        music_box.append(button_box)  # Кнопки сверху
        music_box.append(self.track_label)  # Трек снизу

# Добавляем музыкальный блок в основной контейнер
        main_box.append(music_box)

# Добавьте в initialize_current_values():
        self.track_label.set_text(self.get_current_track())


        # Яркость
        brightness_box = Gtk.Box(orientation=VERTICAL, spacing=4)
        brightness_label = Gtk.Label(label="Яркость")
        brightness_label.add_css_class("section-label")
        self.brightness_scale = Gtk.Scale(orientation=HORIZONTAL)
        self.brightness_scale.set_range(5, 100)
        self.init_brightness_scale(self.brightness_scale)
        self.brightness_scale.connect('value-changed', self.on_brightness_changed)
        brightness_box.append(brightness_label)
        brightness_box.append(self.brightness_scale)
        controls_box.append(brightness_box)
        
        main_box.append(controls_box)

        self.initialize_current_values()

        # # Системные кнопки
        # system_buttons_box = Gtk.Box(orientation=HORIZONTAL, spacing=8)
        # system_buttons_box.add_css_class("widget-box")
        #
        # # WiFi кнопка
        # wifi_button = Gtk.Button(label="WiFi")
        # wifi_button.connect('clicked', self.open_wifi_control)
        # system_buttons_box.append(wifi_button)
        #
        # # Уведомления кнопка
        # notif_button = Gtk.Button(label="Уведомления")
        # notif_button.connect('clicked', self.toggle_notifications)
        # system_buttons_box.append(notif_button)
        #
        # # Системные действия кнопка
        # system_action_button = Gtk.Button(label="Система")
        # system_action_button.connect('clicked', self.open_system_actions)
        # system_buttons_box.append(system_action_button)
        #
        # main_box.append(system_buttons_box)


# Системные кнопки
        system_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        system_buttons_box.add_css_class("widget-box")

# Выравнивание контейнера по центру
        system_buttons_box.set_halign(Gtk.Align.CENTER)
        system_buttons_box.set_hexpand(False)  # Не растягивать на всю ширину

# Вложенный контейнер для кнопок (чтобы они не растягивались)
        button_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_container.set_halign(Gtk.Align.CENTER)

# WiFi кнопка
        wifi_button = Gtk.Button(label="WiFi")
        wifi_button.connect('clicked', self.open_wifi_control)
        button_container.append(wifi_button)

# Уведомления кнопка
        notif_button = Gtk.Button(label="Уведомления")
        notif_button.connect('clicked', self.toggle_notifications)
        button_container.append(notif_button)

# Системные действия кнопка
        system_action_button = Gtk.Button(label="Система")
        system_action_button.connect('clicked', self.open_system_actions)
        button_container.append(system_action_button)

# Добавляем контейнер с кнопками в основной контейнер
        system_buttons_box.append(button_container)

# Добавляем системный блок в основной контейнер
        main_box.append(system_buttons_box)


        # Запуск обновлений
        self.update_time()
        GLib.timeout_add(1000, self.update_time)
        self.update_system_info()
        GLib.timeout_add(2000, self.update_system_info)

    def update_time(self):
        now = datetime.now()
        self.time_label.set_text(now.strftime("%H:%M"))
        self.date_label.set_text(now.strftime("%d %B %Y"))
        return True

    def update_system_info(self):
        # CPU и RAM
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        self.cpu_bar.set_fraction(cpu_percent / 100)
        self.ram_bar.set_fraction(memory.percent / 100)

        # Network speed
        net_io = psutil.net_io_counters()
        time_interval = 1  # 1 second interval
        initial_bytes_sent = net_io.bytes_sent
        initial_bytes_recv = net_io.bytes_recv

        GLib.timeout_add_seconds(time_interval, self.calculate_network_speed, initial_bytes_sent, initial_bytes_recv)

        return True
    
   
    def get_current_track(self):
        try:
            # Получаем информацию о текущем треке
            artist = subprocess.check_output(['playerctl', 'metadata', 'artist'], text=True).strip()
            title = subprocess.check_output(['playerctl', 'metadata', 'title'], text=True).strip()
            return f"{artist} - {title}"
        except subprocess.CalledProcessError:
            return "Музыка не играет"

    def music_control(self, action):
        try:
            subprocess.run(['playerctl', action], check=True)
            # Обновляем информацию о треке после действия
            current_track = self.get_current_track()
            self.track_label.set_text(current_track)
        except subprocess.CalledProcessError:
            pass


    # def init_volume_scale(self, scale):
    #     try:
    #         # Get current volume
    #         output = subprocess.check_output(['wpctl', 'status'], stderr=subprocess.DEVNULL).decode()
    #         match = re.search(r'Volume: (\d+)%', output)
    #         if match:
    #             current_volume = int(match.group(1))
    #             scale.set_value(current_volume)
    #     except Exception:
    #         scale.set_value(50)  # Default value
    #
    # def init_brightness_scale(self, scale):
    #     try:
    #         # Get current brightness
    #         output = subprocess.check_output(['brightnessctl', 'i'], stderr=subprocess.DEVNULL).decode()
    #         match = re.search(r'Current brightness: (\d+)%', output)
    #         if match:
    #             current_brightness = int(match.group(1))
    #             scale.set_value(current_brightness)
    #     except Exception:
    #         scale.set_value(50)  # Default value
    def initialize_current_values(self):
    # Получение текущей громкости
        try:
            volume_output = subprocess.check_output(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'], 
                                                    text=True).strip()
            current_volume = float(volume_output.split(':')[1]) * 100
            self.volume_scale.set_value(current_volume)
        except:
            self.volume_scale.set_value(50)
        
        # Получение текущей яркости
        try:
            brightness_output = subprocess.check_output(['brightnessctl', 'g'], text=True).strip()
            max_brightness = subprocess.check_output(['brightnessctl', 'm'], text=True).strip()
            current_brightness = int(float(brightness_output) / float(max_brightness) * 100)
            self.brightness_scale.set_value(current_brightness)
        except:
            self.brightness_scale.set_value(50)    


    def init_volume_scale(self, scale):
        try:
            # Используем amixer для получения текущей громкости
            output = subprocess.check_output(['amixer', 'get', 'Master'], text=True)
            match = re.search(r'\[(\d+)%\]', output)
            if match:
                current_volume = int(match.group(1))
                scale.set_value(current_volume)
        except Exception:
            scale.set_value(50)  # Значение по умолчанию

    def init_brightness_scale(self, scale):
        try:
            # Получаем текущую яркость через файловую систему
            with open('/sys/class/backlight/intel_backlight/brightness', 'r') as f:
                current = int(f.read().strip())
            with open('/sys/class/backlight/intel_backlight/max_brightness', 'r') as f:
                maximum = int(f.read().strip())
            
            brightness_percentage = (current / maximum) * 100
            scale.set_value(brightness_percentage)
        except Exception:
            scale.set_value(50)  # Значение по умолчанию



    def calculate_network_speed(self, initial_bytes_sent, initial_bytes_recv):
            # Get current network stats
            net_io = psutil.net_io_counters()
            
            # Calculate speeds
            sent_speed = (net_io.bytes_sent - initial_bytes_sent) / (1024 * 1024)  # MB/s
            recv_speed = (net_io.bytes_recv - initial_bytes_recv) / (1024 * 1024)  # MB/s
            total_speed = sent_speed + recv_speed

            # Update progress bar and label
            # Assuming max speed is 100 Mbps for visualization
            max_speed = 100  # Mbps
            normalized_speed = min(total_speed * 8, max_speed) / max_speed
            self.network_bar.set_fraction(normalized_speed)
            
            # Format speed display
            speed_text = f"↑ {sent_speed:.2f} MB/s | ↓ {recv_speed:.2f} MB/s"
            self.network_speed_label.set_text(speed_text)

            return False  # Stop the timeout



    def on_volume_changed(self, scale):
        volume = int(scale.get_value())
        try:
            subprocess.run(['wpctl', 'set-volume', '@DEFAULT_AUDIO_SINK@', f'{volume/100}'], 
                           stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError:
            pass

    def on_brightness_changed(self, scale):
        brightness = int(scale.get_value())
        try:
            subprocess.run(['brightnessctl', 's', f'{brightness}%'], 
                           stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError:
            pass

    def open_wifi_control(self, button):
        try:
            subprocess.Popen(['nm-connection-editor'], stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def toggle_notifications(self, button):
        try:
            subprocess.run(['swaync-client', '-t', '-sw'], stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def open_system_actions(self, button):
        try:
            # Use bash to execute the script
            subprocess.Popen(['bash', '/home/mars/wayland/scripts/hyprsys.sh'], 
                             stderr=subprocess.PIPE, 
                             stdout=subprocess.PIPE)
        except Exception as e:
            print(f"Exception: {e}")

class SystemMonitor(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='org.example.system-monitor')

    def do_activate(self):
        win = SystemMonitorWindow(application=self)
        win.present()

def main():
    app = SystemMonitor()
    try:
        app.run(None)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
