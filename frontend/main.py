import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from screens.login_screen import LoginScreen
from screens.dashboard_screen import DashboardScreen
from screens.project_screen import ProjectScreen
from screens.network_screen import NetworkScreen
from screens.gantt_screen import GanttScreen
from screens.users_screen import UsersScreen

class NetzplanApp(App):
    token = None
    current_user = None
    current_project = None
    current_task = None

    def build(self):
        self.title = "Netzplan App"
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(ProjectScreen(name="project"))
        sm.add_widget(NetworkScreen(name="network"))
        sm.add_widget(GanttScreen(name="gantt"))
        sm.add_widget(UsersScreen(name="users"))
        return sm

if __name__ == "__main__":
    NetzplanApp().run()