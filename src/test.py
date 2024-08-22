import commands
import icons
from rich import print

cmd = commands.draw_icon(icons.ALARM_CHECK)
print(commands.parse(cmd))

cmd = commands.draw_icon_bar(253, 531, 234, 13)
print(commands.parse(cmd))
