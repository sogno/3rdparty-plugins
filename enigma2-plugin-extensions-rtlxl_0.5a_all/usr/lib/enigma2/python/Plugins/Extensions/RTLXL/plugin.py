from Plugins.Plugin import PluginDescriptor
import rtlxl
def main(session, servicelist, **kwargs):
 try:
  session.open(rtlxl.RTLXLMENU)
 except:
  import traceback
  traceback.print_exc()

def Plugins(**kwargs):
 return PluginDescriptor(name = "RTLXL",
  description = "Bekijk rtl netTV op je E2-stb",
  where = [PluginDescriptor.WHERE_EXTENSIONSMENU],
  fnc = main)