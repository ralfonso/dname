#!/usr/bin/python

# 2009 Ryan Roemmich
# strut/positioning code borrowed from the visibility app (http://code.l3ib.org/?p=visibility-python.git;a=summary)

import gtk
import wnck
import os
import pango
from optparse import OptionParser

class Dname:
    def position(self):
        edges = {
                'top_left':gtk.gdk.GRAVITY_NORTH_WEST,
                'top_center':gtk.gdk.GRAVITY_NORTH,
                'top_right':gtk.gdk.GRAVITY_NORTH_EAST,
                'bottom_left':gtk.gdk.GRAVITY_SOUTH_WEST,
                'bottom_center':gtk.gdk.GRAVITY_SOUTH,
                'bottom_right':gtk.gdk.GRAVITY_SOUTH_EAST
        }

        edge = self.options.edge.split('_')
        edge_gap_x = self.options.edge_gap_x
        edge_gap_y = self.options.edge_gap_y

        #self.window.resize(1,1)
        width, height = self.window.get_size()

        if edge[0] == 'top':
            y = edge_gap_y
        else:
            y = gtk.gdk.screen_height() - height - edge_gap_y

        if edge[1] == 'left':
            x = edge_gap_x
        elif edge[1] == 'center':
            x = (gtk.gdk.screen_width() - width) / 2
        else:
            x = gtk.gdk.screen_width() - width - edge_gap_x

        self.window.move(x, y)
        self.strut_set()

    def strut_unset(self):
        self.window.window.property_delete('_NET_WM_STRUT_PARTIAL')

    def strut_set(self):
        if not self.options.strut: return

        w, h = self.window.get_size()
        x, y = self.window.get_position()

        top = 0
        bottom = 0
        left = 0
        right = 0

        left_start_y = 0
        left_end_y = 0

        right_start_y = 0
        right_end_y = 0

        top_start_x = 0
        top_end_x = 0

        bottom_start_x = 0
        bottom_end_x = 0
        
        edge = self.options.edge.split('_')
        edge_gap_x = self.options.edge_gap_x
        edge_gap_y = self.options.edge_gap_y

        if edge[0] == 'top':
            top = h + edge_gap_y
            top_start_x = x
            top_end_x = x + w
        else:
            bottom = h + edge_gap_y
            bottom_start_x = x
            bottom_end_x = x + w

        if self.window.window:
            self.window.window.property_change('_NET_WM_STRUT_PARTIAL', 'CARDINAL', 32, gtk.gdk.PROP_MODE_REPLACE, [left, right, top, bottom, left_start_y, left_end_y, right_start_y, right_end_y, top_start_x, top_end_x, bottom_start_x, bottom_end_x])

    def workspace_active_changed(self, screen, previous):
        self.workspace_active = screen.get_active_workspace()
        font_desc = pango.FontDescription(self.options.font)

        # tertiary hack! assign the proper function based on the option given
        desktop_func = self.options.use_numbers and self.workspace_active.get_number or self.workspace_active.get_name
            
        markup = '<span font_desc="%s" color="%s">%s</span>' % (font_desc,self.options.text_color,desktop_func())
        self.label.set_markup(markup)
        new_x, new_y = self.label.get_layout().get_pixel_size()
        self.window.resize(new_x + (self.options.padding * 2), new_y + (self.options.padding * 2))
        self.window.show_all()

    def show(self):
        self.window.show()

    def __init__(self,options):
        self.options = options
        self.window = gtk.Window()
        self.window.set_geometry_hints(None,min_height=self.options.height)
        
        try:
            self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.options.bgcolor))
        except ValueError:
            if options.debug:
                print "DEBUG: unable to parse bgcolor name"
            self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))

        self.hbox = gtk.HBox()

        self.label = gtk.Label()
        self.label.set_use_markup(True)
        self.label.set_alignment(0.5,0.5)
        self.label.set_justify(gtk.JUSTIFY_CENTER)

        self.hbox.add(self.label)
        #self.window.add(self.label)
        
        self.window.add(self.hbox)
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
        self.window.set_keep_below(True)

        self.window.stick()
        self.window.set_border_width(self.options.padding)

def main():
    edges = [ 'top_left', 'top_center', 'top_right', 'bottom_left', 'bottom_center', 'bottom_right' ] 

    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)

    parser.add_option('--height',dest="height",help='set minimum height',default=24,type="int")
    parser.add_option('--padding',dest="padding",default=6,type="int",
                      help='padding between label and window edge')
    parser.add_option('--edge',dest="edge",default='bottom_left',choices=edges,
                      help='where to place the window "{top,bottom}_{left,center,right}"')
    parser.add_option('-d', "--debug", dest="debug",action="store_true",
                      help="print extra info",default=False)
    parser.add_option('-f','--font',dest='font',
                      help="select the font to use for the display. xft specifications: 'Lucida Grande 10'",default="Sans 8")
    parser.add_option('--gapx',dest='edge_gap_x',
                      help="horizontal spacing from the edge",default=0,type="int")
    parser.add_option('--gapy',dest='edge_gap_y',
                      help="vertical spacing from the edge",default=0,type="int")
    parser.add_option('--noreserve',dest='strut',action="store_false",
                      help="allow apps to be maximized over the dname window")
    parser.add_option('--color',dest='text_color',default='white',                          
                      help='set the text color')
    parser.add_option('--bgcolor',dest='bgcolor',default='black',
                      help='set the background color')
    parser.add_option('--numbers',dest='use_numbers',action='store_true',
                        help='use desktop numbers instead of names',default=False) 

    (options, args) = parser.parse_args()

    dname = Dname(options)
    screen = wnck.screen_get_default()
    screen.force_update()
    gtk.gdk.error_trap_push()

    screen.connect('active-workspace-changed', dname.workspace_active_changed)

    # call the event once to set the current workspace name
    dname.workspace_active_changed(screen,None)

    dname.position()
    dname.show()
    gtk.main()        

if __name__ == '__main__':
    main()
