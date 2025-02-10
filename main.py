import tkinter as tk
from tkinter import ttk, PhotoImage, simpledialog
from datetime import datetime, timedelta
import re
import os
import sys
import json

class MediviaAnalyzer(tk.Tk):
    def __init__(self):
        super().__init__()

        # Set up dark theme
        self.style = ttk.Style()
        self.style.theme_use('default')
        
        # Configure dark theme colors
        bg_color = '#2b2b2b'
        fg_color = '#ffffff'
        accent_color = '#404040'
        hover_color = '#353535'
        scroll_color = '#505050'
        
        self.configure(bg=bg_color)
        
        # Configure styles with consistent dark theme
        self.style.configure('TFrame', background=bg_color)
        self.style.configure('TLabel', background=bg_color, foreground=fg_color)
        self.style.configure('Large.TLabel',
                           background=bg_color,
                           foreground=fg_color,
                           font=('TkDefaultFont', 24))
        self.style.configure('Medium.TLabel',
                    background=bg_color,
                    foreground=fg_color,
                    font=('TkDefaultFont', 14))
        
        # Custom button style
        self.style.configure('Rounded.TButton',
                           background=accent_color,
                           foreground=fg_color,
                           padding=(15, 8),
                           relief='flat',
                           borderwidth=0)
        self.style.map('Rounded.TButton',
                      background=[('active', hover_color)])
        
        # Custom notebook style
        self.style.configure('Custom.TNotebook',
                           background=bg_color,
                           borderwidth=0)
        self.style.configure('Custom.TNotebook.Tab',
                           background=accent_color,
                           foreground=fg_color,
                           padding=[10, 5],
                           borderwidth=0)
        self.style.map('Custom.TNotebook.Tab',
                      background=[('selected', hover_color)],
                      foreground=[('selected', fg_color)])
        
        # Custom treeview style
        self.style.configure('Custom.Treeview',
                           background=accent_color,
                           foreground=fg_color,
                           fieldbackground=accent_color,
                           borderwidth=0,
                           font=('Helvetica', 11),
                           relief='flat')
        self.style.configure('Custom.Treeview.Heading',
                           background=accent_color,
                           foreground=fg_color,
                           relief='flat',
                           font=('Helvetica', 12, 'bold'),
                           borderwidth=6)
        self.style.map('Custom.Treeview.Heading',
                      background=[('active', hover_color)])
        
        # Custom scrollbar style
        self.style.configure('Custom.Vertical.TScrollbar',
                           background=scroll_color,
                           arrowcolor=fg_color,
                           bordercolor=bg_color,
                           troughcolor=bg_color,
                           relief='flat',
                           borderwidth=0)
        self.style.map('Custom.Vertical.TScrollbar',
                      background=[('active', hover_color),
                                ('pressed', hover_color)])
        
        # Custom entry style with rounded corners and white cursor
        self.style.configure('Rounded.TEntry',
                           background=accent_color,
                           foreground=fg_color,
                           fieldbackground=accent_color,
                           insertcolor=fg_color,  # White cursor
                           borderwidth=0,
                           relief='flat',
                           padding=(10, 10))
        
        # Load database
        self.load_database()
        
        self.title("Medivia Analyzer")
        self.geometry("900x600")
        self.minsize(900, 600)  # Adjust these values as needed
        self.iconphoto(False, PhotoImage(file=self.resource_path('analyzer.ico')))

        # Initialize data structures
        self.monster_kills = {}
        self.loot_counts = {}
        self.custom_item_prices = {}
        self.total_gold = 0
        self.total_exp = 0
        self.last_update = None
        self.start_time = datetime.now()
        self.last_position = 0
        self.log_file = os.path.expanduser("~/medivia/Loot.txt")
        self.check_interval = 10000
        self.resize_timer = None
        self.monster_drops = {}  # Format: {monster_name: {item_name: [(quantity, count)]}}
        self.item_sources = {}   # Format: {item_name: set(monster_names)}

        self.setup_ui()
        self.load_settings()
        self.update_timer()
        self.setup_about_tab()
        self.bind('<Configure>', self.on_resize)
        
        self.check_file()
        self.after(self.check_interval, self.periodic_check)


    def setup_ui(self):
        # Top frame for session info, stats, and reset button
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        # Add Export button
        export_button = ttk.Button(
            top_frame, text="Export", style='Rounded.TButton', command=self.export_session
        )
        export_button.pack(side=tk.RIGHT, padx=(10, 0))

        # Stats frame on the left
        stats_frame = ttk.Frame(top_frame)
        stats_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.session_label = ttk.Label(stats_frame, text="Session Time: 00:01:01", font=('TkDefaultFont', 16))
        self.session_label.pack(side=tk.LEFT)

        # Gold stats
        gold_frame = ttk.Frame(stats_frame)
        gold_frame.pack(side=tk.LEFT, padx=20)
        self.total_gold_label = ttk.Label(gold_frame, text=f"Total Gold: {1351:,}", font=('TkDefaultFont', 16))
        self.total_gold_label.pack()

        # Experience stats
        exp_frame = ttk.Frame(stats_frame)
        exp_frame.pack(side=tk.LEFT)
        self.total_exp_label = ttk.Label(exp_frame, text=f"Total Exp: {4900:,}", font=('TkDefaultFont', 16))
        self.total_exp_label.pack()

        reset_button = ttk.Button(top_frame, text="Reset", style='Rounded.TButton', command=self.reset_analyzer)
        reset_button.pack(side=tk.RIGHT)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self, style='Custom.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.notebook.pack_propagate(False)  # Prevent automatic expansion
        self.notebook.configure(height=200)  # Set a smaller minimum height

        # Loot tab
        loot_frame = ttk.Frame(self.notebook)
        self.notebook.add(loot_frame, text="Loot Items")

        # Modified loot tree to include price columns
        self.loot_tree = ttk.Treeview(loot_frame, 
                                    columns=("Item", "Quantity", "Price", "Total"),
                                    show="headings",
                                    style='Custom.Treeview')
        self.loot_tree.heading("Item", text="Item", command=lambda: self.treeview_sort_column(self.loot_tree, "Item", False))
        self.loot_tree.heading("Quantity", text="Quantity", command=lambda: self.treeview_sort_column(self.loot_tree, "Quantity", False))
        self.loot_tree.heading("Price", text="Price", command=lambda: self.treeview_sort_column(self.loot_tree, "Price", False))
        self.loot_tree.heading("Total", text="Total", command=lambda: self.treeview_sort_column(self.loot_tree, "Total", False))
        
        self.loot_tree.column("Item", width=200, anchor='center')
        self.loot_tree.column("Quantity", width=100, anchor='center')
        self.loot_tree.column("Price", width=100, anchor='center')
        self.loot_tree.column("Total", width=100, anchor='center')
        
        # Monsters tab with experience columns
        monsters_frame = ttk.Frame(self.notebook)
        self.notebook.add(monsters_frame, text="Monster Kills")

        self.monster_tree = ttk.Treeview(monsters_frame, 
                                       columns=("Monster", "Kills", "Exp/Kill", "Total Exp"),
                                       show="headings",
                                       style='Custom.Treeview')
        self.monster_tree.heading("Monster", text="Monster", command=lambda: self.treeview_sort_column(self.monster_tree, "Monster", False))
        self.monster_tree.heading("Kills", text="Kills", command=lambda: self.treeview_sort_column(self.monster_tree, "Kills", False))
        self.monster_tree.heading("Exp/Kill", text="Exp/Kill", command=lambda: self.treeview_sort_column(self.monster_tree, "Exp/Kill", False))
        self.monster_tree.heading("Total Exp", text="Total Exp", command=lambda: self.treeview_sort_column(self.monster_tree, "Total Exp", False))
        
        self.monster_tree.column("Monster", width=200, anchor='center')
        self.monster_tree.column("Kills", width=100, anchor='center')
        self.monster_tree.column("Exp/Kill", width=100, anchor='center')
        self.monster_tree.column("Total Exp", width=100, anchor='center')

        # Create context menus for loot and monster tables
        self.loot_context_menu = tk.Menu(self, tearoff=0)
        self.loot_context_menu.add_command(
            label="Exclude Item",
            command=lambda: self.exclude_from_loot()
        )
        self.loot_context_menu.add_separator()
        self.loot_context_menu.add_command(
            label="Search Wiki",
            command=lambda: self.search_wiki(self.loot_tree)
        )
        self.loot_tree.bind('<Button-3>', self.show_loot_context_menu)
        
        self.monster_context_menu = tk.Menu(self, tearoff=0)
        self.monster_context_menu.add_command(
            label="Exclude Monster",
            command=lambda: self.exclude_from_monsters()
        )
        self.monster_context_menu.add_separator()
        self.monster_context_menu.add_command(
            label="Search Wiki",
            command=lambda: self.search_wiki(self.monster_tree)
        )
        self.monster_tree.bind('<Button-3>', self.show_monster_context_menu)
        
        # Add double-click binding for price editing
        self.loot_tree.bind('<Double-1>', self.edit_item_price)

        # Exclude tab
        exclude_frame = ttk.Frame(self.notebook)
        self.notebook.add(exclude_frame, text="Exclude")

        # Create horizontal frame to hold both sections side by side
        exclude_horizontal_frame = ttk.Frame(exclude_frame)
        exclude_horizontal_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Items section (left side)
        exclude_items_frame = ttk.Frame(exclude_horizontal_frame)
        exclude_items_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Items input frame
        items_input_frame = ttk.Frame(exclude_items_frame)
        items_input_frame.pack(fill=tk.X, pady=5)

        self.excluded_items_var = tk.StringVar()
        self.excluded_items_entry = ttk.Entry(
            items_input_frame, 
            textvariable=self.excluded_items_var, 
            style='Rounded.TEntry'
        )
        self.excluded_items_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        add_item_button = ttk.Button(
            items_input_frame, 
            text="Add Item", 
            style='Rounded.TButton',
            command=lambda: self.add_to_exclude_list(self.excluded_items_tree, self.excluded_items_var.get())
        )
        add_item_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Bind Enter key to add item
        self.excluded_items_entry.bind('<Return>', 
            lambda e: self.add_to_exclude_list(self.excluded_items_tree, self.excluded_items_var.get())
        )
        
        # Items list with scrollbar
        excluded_items_tree_frame = ttk.Frame(exclude_items_frame)
        excluded_items_tree_frame.pack(fill=tk.BOTH, expand=True)

        self.excluded_items_tree = ttk.Treeview(
            excluded_items_tree_frame,
            columns=("Item",),
            show="headings",
            style='Custom.Treeview'
        )
        self.excluded_items_tree.heading("Item", text="Item")
        self.excluded_items_tree.column("Item", width=200, anchor='center')

        # Create context menu for items list
        self.excluded_items_context_menu = tk.Menu(self, tearoff=0)
        self.excluded_items_context_menu.add_command(
            label="Remove", 
            command=lambda: self.remove_selected_item(self.excluded_items_tree)
        )
        self.excluded_items_context_menu.add_separator()
        self.excluded_items_context_menu.add_command(
            label="Search Wiki",
            command=lambda: self.search_wiki(self.excluded_items_tree)
        )
        self.excluded_items_tree.bind('<Button-3>', self.show_context_menu)
        self.excluded_items_tree.bind('<Double-1>', self.edit_excluded_item)

        # Monsters section
        exclude_monsters_frame = ttk.Frame(exclude_horizontal_frame)
        exclude_monsters_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        excluded_monsters_tree_frame = ttk.Frame(exclude_monsters_frame)
        excluded_monsters_tree_frame.pack(fill=tk.BOTH, expand=True)

        monsters_input_frame = ttk.Frame(excluded_monsters_tree_frame)
        monsters_input_frame.pack(fill=tk.X, pady=5)

        self.excluded_monsters_var = tk.StringVar()
        self.excluded_monsters_entry = ttk.Entry(
            monsters_input_frame, 
            textvariable=self.excluded_monsters_var, 
            style='Rounded.TEntry'
        )
        self.excluded_monsters_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        add_monster_button = ttk.Button(
            monsters_input_frame, 
            text="Add Monster", 
            style='Rounded.TButton',
            command=lambda: self.add_to_exclude_list(self.excluded_monsters_tree, self.excluded_monsters_var.get())
        )
        add_monster_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Bind Enter key to add monster
        self.excluded_monsters_entry.bind('<Return>', 
            lambda e: self.add_to_exclude_list(self.excluded_monsters_tree, self.excluded_monsters_var.get())
        )

        self.excluded_monsters_tree = ttk.Treeview(
            excluded_monsters_tree_frame, 
            columns=("Monster",), 
            show="headings", 
            style='Custom.Treeview'
        )
        self.excluded_monsters_tree.heading("Monster", text="Monster")
        self.excluded_monsters_tree.column("Monster", width=200, anchor='center')

        # Create context menu for monsters list
        self.excluded_monsters_context_menu = tk.Menu(self, tearoff=0)
        self.excluded_monsters_context_menu.add_command(
            label="Remove", 
            command=lambda: self.remove_selected_item(self.excluded_monsters_tree)
        )
        self.excluded_monsters_context_menu.add_separator()
        self.excluded_monsters_context_menu.add_command(
            label="Search Wiki",
            command=lambda: self.search_wiki(self.excluded_monsters_tree)
        )
        self.excluded_monsters_tree.bind('<Button-3>', self.show_context_menu)
        self.excluded_monsters_tree.bind('<Double-1>', self.edit_excluded_item)
        
        # Customize tab
        customize_frame = ttk.Frame(self.notebook)
        self.notebook.add(customize_frame, text="Custom Prices")
        prices_tree_frame = ttk.Frame(customize_frame)
        prices_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Input frame for item and price
        input_frame = ttk.Frame(prices_tree_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        # Item name input
        item_label = ttk.Label(input_frame, text="Item Name:", style='Medium.TLabel') 
        item_label.pack(side=tk.LEFT, padx=(0,5))

        self.custom_item_var = tk.StringVar()
        item_entry = ttk.Entry(
            input_frame,
            textvariable=self.custom_item_var,
            style='Rounded.TEntry'
        )
        item_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,10))

        # Price input 
        price_label = ttk.Label(input_frame, text="Price:", style='Medium.TLabel')
        price_label.pack(side=tk.LEFT, padx=(0,5))

        self.custom_price_var = tk.StringVar(value='0') 
        vcmd = (self.register(self.validate_price_input), '%P')
        price_entry = ttk.Entry(
            input_frame,
            textvariable=self.custom_price_var,
            style='Rounded.TEntry',
            validate='key',
            validatecommand=vcmd
        )
        price_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Bind Enter key to both entries
        item_entry.bind('<Return>', lambda e: self.add_custom_price())
        price_entry.bind('<Return>', lambda e: self.add_custom_price())

        # Add button
        add_button = ttk.Button(
            input_frame,
            text="Add",
            style='Rounded.TButton',
            command=self.add_custom_price
        )
        add_button.pack(side=tk.LEFT, padx=(10,0))

        # Custom prices table
        self.custom_prices_tree = ttk.Treeview(
            prices_tree_frame,
            columns=("Item", "Price"),
            show="headings",
            style='Custom.Treeview'
        )

        self.custom_prices_tree.heading("Item", text="Item")
        self.custom_prices_tree.heading("Price", text="Price") 
        self.custom_prices_tree.column("Item", width=200, anchor='center')
        self.custom_prices_tree.column("Price", width=100, anchor='center')
        # self.custom_prices_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

        # Context menu
        self.prices_context_menu = tk.Menu(self, tearoff=0)
        self.prices_context_menu.add_command(
            label="Remove",
            command=self.remove_custom_price
        )
        self.prices_context_menu.add_separator()
        self.prices_context_menu.add_command(
            label="Search Wiki",
            command=lambda: self.search_wiki(self.custom_prices_tree)
        )
        self.custom_prices_tree.bind('<Button-3>', self.show_prices_context_menu)
        self.custom_prices_tree.bind('<Double-1>', self.edit_custom_price_entry)

        # Add scrollbars
        for tree, frame in [(self.monster_tree, monsters_frame), (self.loot_tree, loot_frame), (self.custom_prices_tree, prices_tree_frame), (self.excluded_monsters_tree, excluded_monsters_tree_frame), (self.excluded_items_tree, excluded_items_tree_frame)]:
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview, style='Custom.Vertical.TScrollbar')
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(fill=tk.BOTH, expand=True)

        # Add hover effects to treeview rows
        for tree in [self.monster_tree, self.loot_tree, self.custom_prices_tree, self.excluded_monsters_tree, self.excluded_items_tree]:
            self.add_hover_effect(tree)

        # Add data structures for tracking stats history
        self.gold_history = []  # Will store (timestamp, value) tuples
        self.exp_history = []   # Will store (timestamp, value) tuples
    
        # Add bottom frame for stats display
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10, side=tk.BOTTOM)

        # Set a minimum height for the bottom frame
        bottom_frame.update_idletasks()  # Update to get current size

        # Stats containers with larger font
        stats_style = {'font': ('TkDefaultFont', 16)}
        
        # Gold per hour container
        gold_stats = ttk.Frame(bottom_frame)
        gold_stats.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.gold_per_hour_label = ttk.Label(gold_stats, text=f"Gold/Hour: {79271:,}", **stats_style)
        self.gold_per_hour_label.pack(side=tk.TOP)
        
        # Create gold graph widget
        self.gold_graph = self.create_graph_widget(gold_stats, "Gold/Hour")
        self.gold_graph.pack(side=tk.TOP, padx=10, pady=(5,0))

        # Experience per hour container
        exp_stats = ttk.Frame(bottom_frame)
        exp_stats.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
        self.exp_per_hour_label = ttk.Label(exp_stats, text=f"Exp/Hour: {287513:,}", **stats_style)
        self.exp_per_hour_label.pack(side=tk.TOP)
        
        # Create exp graph widget
        self.exp_graph = self.create_graph_widget(exp_stats, "Exp/Hour")
        self.exp_graph.pack(side=tk.TOP, padx=10, pady=(5,0))

    def show_loot_context_menu(self, event):
        item = self.loot_tree.identify_row(event.y)
        if item:
            self.loot_tree.selection_set(item)
            self.loot_context_menu.post(event.x_root, event.y_root)

    def show_monster_context_menu(self, event):
        item = self.monster_tree.identify_row(event.y)
        if item:
            self.monster_tree.selection_set(item)
            self.monster_context_menu.post(event.x_root, event.y_root)
            
    def exclude_from_loot(self):
        selected = self.loot_tree.selection()
        if selected:
            item = self.loot_tree.item(selected[0])['values'][0]
            self.add_to_exclude_list(self.excluded_items_tree, item)
            # Remove from loot counts and update display
            if item in self.loot_counts:
                del self.loot_counts[item]
            self.update_stats()
            self.calculate_totals()

    def exclude_from_monsters(self):
        selected = self.monster_tree.selection()
        if selected:
            monster = self.monster_tree.item(selected[0])['values'][0]
            self.add_to_exclude_list(self.excluded_monsters_tree, monster)
            # Remove from monster kills and update display
            if monster in self.monster_kills:
                del self.monster_kills[monster]
            self.update_stats()
            self.calculate_totals()

    def edit_item_price(self, event):
        item = self.loot_tree.identify_row(event.y)
        column = self.loot_tree.identify_column(event.x)
        
        # Only allow editing the price column (#3)
        if not item or column != '#3':
            return
        
        # Get item info
        item_name = self.loot_tree.item(item)['values'][0]
        current_price = self.get_item_price(item_name)
        
        # Create entry widget with white text color
        entry = ttk.Entry(self.loot_tree, justify='center')
        entry.configure(foreground='black', background='#404040')
        entry.insert(0, str(current_price))

        # Add validation
        def validate_input(char):
            return char.isdigit()
        
        validation = self.register(validate_input)
        entry.configure(
            validate='key',
            validatecommand=(validation, '%S')
        )
        
        # Position entry widget
        x, y, w, h = self.loot_tree.bbox(item, column)
        entry.place(x=x, y=y, width=w, height=h)
        entry.select_range(0, tk.END)
        entry.focus()
        
        def save_price(event=None):
            try:
                new_price = int(entry.get())
                self.custom_item_prices[item_name] = new_price
                entry.destroy()
                self.update_custom_prices_tree()
                self.update_stats()
                self.calculate_totals()
            except ValueError:
                entry.destroy()
        
        entry.bind('<Return>', save_price)
        entry.bind('<FocusOut>', save_price)
        entry.bind('<Escape>', save_price)

    def validate_price_input(self, new_value):
        return new_value == "" or new_value.isdigit()

    def on_resize(self, event):
        # Force graph redraw on window resize
        current_time = datetime.now()
        elapsed_seconds = (current_time - self.start_time).total_seconds()
        if elapsed_seconds > 0:
            gold_per_hour = int((self.total_gold * 3600) / elapsed_seconds)
            exp_per_hour = int((self.total_exp * 3600) / elapsed_seconds)
            
            self.update_graph(self.gold_graph, gold_per_hour, current_time)
            self.update_graph(self.exp_graph, exp_per_hour, current_time)

        # Cancel previous timer if it exists
        if self.resize_timer is not None:
            self.after_cancel(self.resize_timer)
        
        # Set new timer
        self.resize_timer = self.after(500, self.save_after_resize)
        
    def save_after_resize(self):
        self.resize_timer = None
        self.save_settings()

    def add_custom_price(self):
        item = self.custom_item_var.get().strip().lower()
        price = self.custom_price_var.get().strip()
        if not item or not price:
            return
        try:
            price = int(price) if price else 0
        except ValueError:
            price = 0
        
        self.custom_item_prices[item] = price
        self.custom_item_var.set("")
        self.custom_price_var.set("0")
        self.update_custom_prices_tree()

        self.save_settings()
        self.update_stats()
        self.calculate_totals()

    def show_prices_context_menu(self, event):
        item = self.custom_prices_tree.identify_row(event.y)
        if item:
            self.custom_prices_tree.selection_set(item)
            self.prices_context_menu.post(event.x_root, event.y_root)

    def remove_custom_price(self):
        selected = self.custom_prices_tree.selection()
        if selected:
            item_id = selected[0]
            item_name = str(self.custom_prices_tree.item(item_id)['values'][0])
            # Remove from prices dictionary
            if item_name in self.custom_item_prices:
                del self.custom_item_prices[item_name]
                print("Removed item:", self.custom_item_prices)
            # Remove from tree
            self.custom_prices_tree.delete(item_id)
            self.update_custom_prices_tree()

            self.save_settings()
            self.update_stats()
            self.calculate_totals()

    def update_custom_prices_tree(self):
        for item in self.custom_prices_tree.get_children():
            self.custom_prices_tree.delete(item)
            
        for item, price in self.custom_item_prices.items():
            self.custom_prices_tree.insert('', tk.END, values=(item, f"{price:,}"))

    def add_to_exclude_list(self, treeview, item):
        if item:
            item = item.strip().lower()
            if item not in [treeview.item(child)['values'][0].lower() for child in treeview.get_children()]:
                item_id = treeview.insert('', tk.END, values=(item, "Remove"))
                if treeview == self.excluded_items_tree:
                    self.excluded_items_var.set("")
                    # Remove excluded item from loot counts and recalculate
                    if item in self.loot_counts:
                        del self.loot_counts[item]
                else:
                    self.excluded_monsters_var.set("")
                    # Remove excluded monster from kills and recalculate
                    if item in self.monster_kills:
                        del self.monster_kills[item]
                
                treeview.tag_bind(item_id, '', lambda e: self.handle_remove_click(e, treeview))

                self.save_settings()
                self.update_stats()
                self.calculate_totals()
                
    def show_context_menu(self, event):
        tree = event.widget
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            if tree == self.excluded_items_tree:
                self.excluded_items_context_menu.post(event.x_root, event.y_root)
            else:
                self.excluded_monsters_context_menu.post(event.x_root, event.y_root)

    def remove_selected_item(self, treeview):
        selected_item = treeview.selection()
        if selected_item:
            item = treeview.item(selected_item)['values'][0]
            treeview.delete(selected_item)

            self.save_settings()
            self.reprocess_log_file()
            self.update_stats()
            self.calculate_totals()

    def reprocess_log_file(self):
        # Clear current counts
        self.monster_kills.clear()
        self.loot_counts.clear()
        
        # Store current position
        current_position = self.last_position
        self.last_position = 0
        
        # Reprocess file
        self.check_file()
        
        # Restore position
        self.last_position = current_position

    def add_custom_item(self):
        item_name = simpledialog.askstring("Add Custom Item", "Enter item name:")
        if item_name:
            item_name = item_name.strip()
            price = simpledialog.askinteger("Add Custom Item", "Enter item price:")
            if price is not None:
                self.custom_item_prices[item_name] = price
                self.save_settings()
                self.update_custom_items_tree()

    def remove_custom_item(self):
        selected_item = self.custom_items_tree.focus()
        if selected_item:
            item_name = self.custom_items_tree.item(selected_item)['values'][0]
            del self.custom_item_prices[item_name]
            self.save_settings()
            self.update_custom_items_tree()

    def update_custom_items_tree(self):
        for item in self.custom_items_tree.get_children():
            self.custom_items_tree.delete(item)

        for item, price in self.custom_item_prices.items():
            self.custom_items_tree.insert('', tk.END, values=(item, price))

    def format_number(self, num):
        """Format large numbers with K/M suffixes"""
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        return f"{int(num):,}"

    def create_graph_widget(self, parent, title):
        frame = ttk.Frame(parent)
        frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        
        canvas = tk.Canvas(frame, height=100, bg='#2b2b2b', highlightthickness=0)
        canvas.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        
        # Add a title label
        title_label = ttk.Label(frame, text=title, style='TLabel')
        title_label.pack(side=tk.TOP)
        
        # Store additional properties with the canvas
        canvas.title = title
        canvas.data_points = []
        canvas.last_update = None
        
        return canvas

    def update_graph(self, canvas, new_value, timestamp):
        # Store the new data point
        canvas.data_points.append((timestamp, new_value))
        
        # Keep only last hour of data
        cutoff_time = timestamp - timedelta(hours=1)
        canvas.data_points = [(t, v) for t, v in canvas.data_points if t > cutoff_time]
        
        # Clear canvas
        canvas.delete('all')
        
        if len(canvas.data_points) < 2:
            return

        # Ensure canvas is updated with current size
        width = canvas.winfo_width() or 200
        height = canvas.winfo_height() or 100
        padding = 25  # Space for labels
        
        # Calculate value range
        values = [v for _, v in canvas.data_points]
        min_val = max(0, min(values))  # Ensure min is not negative
        max_val = max(values)
        value_range = max_val - min_val
        
        # Ensure some minimum range
        if value_range == 0:
            value_range = max(max_val * 0.1, 100)
            min_val = 0
            max_val += value_range
        
        # Draw Y-axis labels (right side)
        num_y_labels = 3
        for i in range(num_y_labels):
            y_pos = padding + (height - 2*padding) * (1 - i/(num_y_labels-1))
            value = min_val + (value_range * i/(num_y_labels-1))
            canvas.create_text(
                width-5, y_pos,
                text=self.format_number(value),
                fill='#ffffff',
                anchor='e',
                font=('TkDefaultFont', 8)
            )
        
        # Draw the line
        coords = []
        earliest_time = canvas.data_points[0][0]
        latest_time = canvas.data_points[-1][0]
        
        if (latest_time - earliest_time).total_seconds() > 0:
            for timestamp, value in canvas.data_points:
                x = padding + (width - 2*padding) * ((timestamp - earliest_time).total_seconds() /
                                                (latest_time - earliest_time).total_seconds())
                y = padding + (height - 2*padding) * (1 - (value - min_val) / value_range)
                coords.extend([x, y])
            
        if len(coords) >= 4:
            canvas.create_line(
                coords,
                fill='#ff4444',
                width=2,
                smooth=True
            )

    def update_timer(self):
        elapsed = datetime.now() - self.start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.session_label.config(text=f"Session Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Update rates
        self.calculate_totals()
        
        # Schedule next update
        self.after(1000, self.update_timer)

    def load_database(self):
        try:
            with open(self.resource_path('db.json'), 'r') as f:
                data = json.load(f)
                self.item_db = {item['name'].lower(): item for item in data['items']}
                self.creature_db = {creature['name'].lower(): creature for creature in data['creatures']}
                print(f"Loaded database with {len(self.item_db)} items and {len(self.creature_db)} creatures.")
        except Exception as e:
            print(f"Error loading database: {e}")
            self.item_db = {}
            self.creature_db = {}

    def periodic_check(self):
        self.check_file()
        self.after(self.check_interval, self.periodic_check)

    def check_file(self):
        try:
            if not os.path.exists(self.log_file):
                return

            with open(self.log_file, 'r', encoding='utf-8') as file:
                file.seek(self.last_position)
                new_lines = file.readlines()
                self.last_position = file.tell()

                log_section_datetime = None
                for line in new_lines:
                    # Extract channel saved date
                    if "Channel saved at" in line:
                        date_str = line.replace("Channel saved at ", "").strip()
                        log_section_datetime = datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y')
                        continue

                    # Skip if we haven't found a channel saved date yet
                    if not log_section_datetime:
                        continue

                    # Extract timestamp from line
                    timestamp_match = re.match(r'(\d{2}:\d{2})', line)
                    if timestamp_match:
                        line_time_str = timestamp_match.group(1)
                        # Create a datetime object for the line by combining current_date with line time
                            
                        try:
                            read_line_hour = int(line_time_str.split(':')[0])
                            read_line_minute = int(line_time_str.split(':')[1])

                            if (log_section_datetime.hour == 0 and read_line_hour == 23):
                                line_datetime = log_section_datetime.replace(
                                    day=log_section_datetime.day - 1,
                                    hour=read_line_hour,
                                    minute=read_line_minute,
                                    second=0,
                                    microsecond=0
                                )
                            else:
                                line_datetime = log_section_datetime.replace(
                                    hour=read_line_hour,
                                    minute=read_line_minute,
                                    second=0,
                                    microsecond=0
                                )
                        except ValueError as e:
                            print(f"ValueError: {e}, Line: {line}")
                            continue # Skip to the next line

                        # Process line if it's after start_time
                        if line_datetime >= self.start_time:
                            self.process_line(line)

                self.update_stats()

        except Exception as e:
            print(f"Error reading file: {e}")

    def normalize_plural(self, word):
        # Remove articles and trim
        word = re.sub(r'^(a|an)\s+', '', word.strip())
        
        # Special cases that should keep their 's'
        keep_s = ['boots', 'legs']
        if word.lower() in keep_s:
            return word
            
        # Handle special plural cases
        if word.endswith('ies'):
            return word[:-3] + 'y'
        elif word.endswith('ves'):
            return word[:-3] + 'f'
        elif word.endswith('s') and not any(word.lower().endswith(x) for x in keep_s):
            return word[:-1]
        
        return word

    def process_line(self, line):
        loot_pattern = r'Loot of ([^:]+): (.*)'
        bag_pattern = r'Content of a bag within the corpse of ([^:]+): (.*)'
        event_pattern = r'Looted (\d+) (\w+) points?'
        
        # Check for regular loot
        loot_match = re.search(loot_pattern, line.strip())
        if loot_match:
            monster_name = loot_match.group(1).strip()
            items_text = loot_match.group(2).strip()
            
            # Update monster kills only if not excluded
            excluded_monsters = [self.excluded_monsters_tree.item(child)['values'][0].lower()
                            for child in self.excluded_monsters_tree.get_children()]
            
            if monster_name not in excluded_monsters:
                self.monster_kills[monster_name] = self.monster_kills.get(monster_name, 0) + 1
            
            self.process_items(items_text, monster_name)
            return
        
        # Check for bag contents
        bag_match = re.search(bag_pattern, line.strip())
        if bag_match:
            current_monster = bag_match.group(1).strip()
            items_text = bag_match.group(2).strip()
            self.process_items(items_text, current_monster)
            return
        
        # Check for event points
        event_match = re.search(event_pattern, line.strip())
        if event_match:
            quantity = int(event_match.group(1))
            point_type = f"{event_match.group(2).lower()} point"
            self.loot_counts[point_type] = self.loot_counts.get(point_type, 0) + quantity
            return

    def process_items(self, items_text, monster_name=None):
        excluded_items = [self.excluded_items_tree.item(child)['values'][0].lower() 
                        for child in self.excluded_items_tree.get_children()]
        
        # Initialize monster tracking
        if monster_name and monster_name not in self.monster_drops:
            self.monster_drops[monster_name] = {}
            
        items = [item.strip().rstrip('.').lower() for item in items_text.split(',')]
        
        for item in items:
            # Handle items with explicit quantities
            quantity_match = re.match(r'^(\d+)\s+(.+?)(?:\.)?$', item)
            if quantity_match:
                quantity = int(quantity_match.group(1))
                item_name = quantity_match.group(2)
            # Handle items with "a" or "an"
            elif item.startswith(('a ', 'an ')):
                quantity = 1
                item_name = item[item.index(' ')+1:]
            else:
                quantity = 1
                item_name = item

            # Normalize item name
            item_name = self.normalize_plural(item_name)
                
            if item_name in ["bag", "empty"] or item_name in excluded_items:
                continue
                
            # Track each drop as a single instance with its quantity
            if monster_name:
                if item_name not in self.monster_drops[monster_name]:
                    self.monster_drops[monster_name][item_name] = []
                # Store just one entry per drop instance
                self.monster_drops[monster_name][item_name].append(quantity)
                
                # Track item sources
                if item_name not in self.item_sources:
                    self.item_sources[item_name] = set()
                self.item_sources[item_name].add(monster_name)
                
            # Update total counts
            if item_name not in excluded_items:
                self.loot_counts[item_name] = self.loot_counts.get(item_name, 0) + quantity

    def calculate_drop_stats(self, item_name, monster_name):
        if monster_name not in self.monster_drops or item_name not in self.monster_drops[monster_name]:
            return None, "0"
            
        kills = self.monster_kills.get(monster_name, 0)
        if kills == 0:
            return None, "0"
            
        # Get all drop instances for this item from this monster
        drop_instances = len(self.monster_drops[monster_name][item_name])
        quantities = self.monster_drops[monster_name][item_name]
        
        # Calculate true drop rate based on number of corpses that dropped the item
        drop_rate = (drop_instances / kills) * 100
        
        # Calculate quantity statistics
        min_qty = min(quantities)
        max_qty = max(quantities)
        avg_qty = sum(quantities) / len(quantities)
        qty_range = f"{min_qty}-{max_qty}" if min_qty != max_qty else str(min_qty)
        
        # Format the statistics string
        stats = f"{drop_rate:.2f}%, avg: {avg_qty:.1f}, range: {qty_range}"
        
        return drop_rate, stats
    
    def calculate_drop_rate(self, item_name):
        if item_name not in self.item_sources:
            return "0%"
            
        total_drops = 0
        total_kills = 0
        
        # Calculate drops across all monsters
        for monster in self.item_sources[item_name]:
            if monster in self.monster_kills:
                total_kills += self.monster_kills[monster]
                if monster in self.monster_drops and item_name in self.monster_drops[monster]:
                    total_drops += len(self.monster_drops[monster][item_name])
                    
        if total_kills == 0:
            return "0%"
            
        drop_rate = (total_drops / total_kills) * 100
        return f"{drop_rate:.2f}%"

    def get_monster_specific_drop_rate(self, item_name, monster_name):
        if monster_name not in self.monster_kills or monster_name not in self.monster_drops:
            return "0%"
            
        kills = self.monster_kills[monster_name]
        drops = self.monster_drops[monster_name].get(item_name, 0)
        
        if kills == 0:
            return "0%"
            
        drop_rate = (drops / kills) * 100
        return f"{drop_rate:.2f}%"

    def get_item_price(self, item_name):
        item_name = item_name.lower()
        if item_name == "gold coin":
            return 1
        elif item_name == "platinum coin":
            return 100
        elif item_name == "crystal coin":
            return 10000
        elif item_name in self.custom_item_prices:
            return self.custom_item_prices[item_name]
        else:
            return self.item_db.get(item_name, {}).get('price', 0)

    def get_monster_exp(self, monster_name):
        return self.creature_db.get(monster_name.lower(), {}).get('exp', 0)

    def calculate_totals(self):
        self.total_gold = sum(count * self.get_item_price(item) for item, count in self.loot_counts.items())
        self.total_exp = sum(kills * self.get_monster_exp(monster) for monster, kills in self.monster_kills.items())
        
        # Calculate per hour rates
        elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        if elapsed_seconds > 0:
            gold_per_hour = int((self.total_gold * 3600) / elapsed_seconds)
            exp_per_hour = int((self.total_exp * 3600) / elapsed_seconds)
        else:
            gold_per_hour = 0
            exp_per_hour = 0

        # Update labels and graphs
        self.total_gold_label.config(text=f"Total Gold: {self.total_gold:,}")
        self.total_exp_label.config(text=f"Total Exp: {self.total_exp:,}")
        self.gold_per_hour_label.config(text=f"Gold/Hour: {gold_per_hour:,}")
        self.exp_per_hour_label.config(text=f"Exp/Hour: {exp_per_hour:,}")
        
        # Update graphs
        current_time = datetime.now()
        
        # Only update graphs if we have new data
        if self.last_update is None or (current_time - self.last_update).total_seconds() >= 60:
            elapsed_seconds = (current_time - self.start_time).total_seconds()
            if elapsed_seconds > 0:
                gold_per_hour = int((self.total_gold * 3600) / elapsed_seconds)
                exp_per_hour = int((self.total_exp * 3600) / elapsed_seconds)
                
                self.update_graph(self.gold_graph, gold_per_hour, current_time)
                self.update_graph(self.exp_graph, exp_per_hour, current_time)
                
                self.last_update = current_time

    def update_stats(self):
        # Clear existing items
        for tree in (self.loot_tree, self.monster_tree):
            for item in tree.get_children():
                tree.delete(item)
                
        # Update loot table
        for item, count in sorted(self.loot_counts.items()):
            price = self.get_item_price(item)
            total = price * count
            drop_rate = self.calculate_drop_rate(item)
            
            self.loot_tree.insert('', tk.END, values=(
                item,
                f"{count:,}",
                f"{price:,}",
                f"{total:,}",
                drop_rate
            ))
            
        # Update monster table
        for monster, kills in sorted(self.monster_kills.items()):
            exp = self.get_monster_exp(monster)
            total_exp = exp * kills
            
            self.monster_tree.insert('', tk.END, values=(
                monster,
                f"{kills:,}",
                f"{exp:,}",
                f"{total_exp:,}"
            ))
            
        self.calculate_totals()

    def treeview_sort_column(self, tree, col, reverse):
        items = [(tree.set(item, col), item) for item in tree.get_children('')]
        
        # Convert counts to numbers for proper sorting
        if col in ("Quantity", "Kills", "Price", "Total", "Exp/Kill", "Total Exp"):
            items = [(int(str(value).replace(',', '')), item) for value, item in items]
        
        items.sort(reverse=reverse)
        
        for index, (val, item) in enumerate(items):
            tree.move(item, '', index)
        
        tree.heading(col, command=lambda: self.treeview_sort_column(tree, col, not reverse))

    def reset_analyzer(self):
        self.monster_kills.clear()
        self.loot_counts.clear()
        self.total_gold = 0
        self.total_exp = 0
        self.start_time = datetime.now()
        self.last_position = 0
        self.update_stats()

        # Clear graph data
        self.gold_graph.data_points = []
        self.exp_graph.data_points = []
        self.last_update = None

    def export_session(self):
        session_datetime = datetime.now().strftime('%y%m%d-%H-%M')
        file_name = f"hunting_session_{session_datetime}.txt"
        
        # Create a list of known event point types
        event_point_types = {'halloween point', 'christmas voucher', 'anniversary token', 'demonic ticket'}
        
        with open(file_name, 'w', encoding='utf-8') as file:
            # Session Summary
            file.write(f"Session Time: {self.session_label.cget('text')}\n")
            file.write(f"Total Gold: {self.total_gold:,}\n")
            file.write(f"Total Exp: {self.total_exp:,}\n")
            file.write(f"Gold/Hour: {self.gold_per_hour_label.cget('text')}\n")
            file.write(f"Exp/Hour: {self.exp_per_hour_label.cget('text')}\n\n")
            
            # Loot Items with Drop Rates
            file.write("Loot Items:\n")
            file.write("-" * 100 + "\n")
            file.write(f"{'Item':<30} {'Count':<10} {'Price':<12} {'Total':<15} {'Drop Rate':<10} {'Sources'}\n")
            file.write("-" * 100 + "\n")
            
            for item, count in sorted(self.loot_counts.items()):
                if item in event_point_types:
                    continue
                    
                price = self.get_item_price(item)
                total = price * count
                
                # Get drop sources and rates with ranges and averages
                sources_info = []
                if item in self.item_sources:
                    for monster in self.item_sources[item]:
                        if monster in self.monster_kills:
                            kills = self.monster_kills[monster]
                            drops = self.monster_drops[monster].get(item, [])
                            if kills > 0 and drops:
                                rate = (len(drops) / kills) * 100
                                min_qty = min(drops)
                                max_qty = max(drops)
                                avg_qty = sum(drops) / len(drops)
                                qty_range = f"{min_qty}-{max_qty}" if min_qty != max_qty else str(min_qty)
                                sources_info.append(
                                    f"{monster} ({rate:.2f}%, avg: {avg_qty:.1f}, range: {qty_range})"
                                )
                
                sources_text = " | ".join(sources_info) if sources_info else "N/A"
                overall_rate = self.calculate_drop_rate(item)
                
                file.write(f"{item:<30} {count:<10} {price:<12,} {total:<15,} {overall_rate:<10} {sources_text}\n")
            
            # Monster Kills with Drop Details
            file.write("\nMonster Kills and Drops:\n")
            file.write("-" * 100 + "\n")
            file.write(f"{'Monster':<25} {'Kills':<8} {'Exp/Kill':<10} {'Total Exp':<15} {'Items Dropped'}\n")
            file.write("-" * 100 + "\n")
            
            for monster, kills in sorted(self.monster_kills.items()):
                exp = self.get_monster_exp(monster)
                total_exp = exp * kills
                
                # Get items dropped by this monster with detailed statistics
                dropped_items = []
                if monster in self.monster_drops:
                    for item, drops in self.monster_drops[monster].items():
                        drop_rate = (len(drops) / kills) * 100
                        min_qty = min(drops)
                        max_qty = max(drops)
                        avg_qty = sum(drops) / len(drops)
                        qty_range = f"{min_qty}-{max_qty}" if min_qty != max_qty else str(min_qty)
                        dropped_items.append(
                            f"{item} ({drop_rate:.2f}%, avg: {avg_qty:.1f}, range: {qty_range})"
                        )
                
                items_text = " | ".join(dropped_items) if dropped_items else "None"
                file.write(f"{monster:<25} {kills:<8} {exp:<10,} {total_exp:<15,} {items_text}\n")
            
            # Excluded Items and Monsters
            file.write("\nExcluded Items:\n")
            for item in self.excluded_items_tree.get_children():
                file.write(f"{self.excluded_items_tree.item(item)['values'][0]}\n")
            
            file.write("\nExcluded Monsters:\n")
            for monster in self.excluded_monsters_tree.get_children():
                file.write(f"{self.excluded_monsters_tree.item(monster)['values'][0]}\n")
            
            file.write("\nCustom Item Prices:\n")
            for item, price in self.custom_item_prices.items():
                file.write(f"{item}: {price:,} gold\n")
            
            print(f"Session data exported to {file_name}")

    def search_wiki(self, treeview):
        selected = treeview.selection()
        if selected:
            item = treeview.item(selected[0])['values'][0]
            url = f"https://wiki.mediviastats.info/index.php?search={item.replace(' ', '+')}"
            import webbrowser
            webbrowser.open(url)

    def save_settings(self):
        settings = {
            'excluded_items': [self.excluded_items_tree.item(child)['values'][0] 
                            for child in self.excluded_items_tree.get_children()],
            'excluded_monsters': [self.excluded_monsters_tree.item(child)['values'][0] 
                                for child in self.excluded_monsters_tree.get_children()],
            'custom_prices': self.custom_item_prices,
            'window_size': {
                'width': self.winfo_width(),
                'height': self.winfo_height()
            }
        }
        
        with open('analyzer_settings.json', 'w') as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open('analyzer_settings.json', 'r') as f:
                settings = json.load(f)
                
                # Restore window size
                if 'window_size' in settings:
                    width = settings['window_size']['width']
                    height = settings['window_size']['height']
                    self.geometry(f"{width}x{height}")
                
                # Restore excluded items
                for item in settings.get('excluded_items', []):
                    self.add_to_exclude_list(self.excluded_items_tree, item)
                
                # Restore excluded monsters
                for monster in settings.get('excluded_monsters', []):
                    self.add_to_exclude_list(self.excluded_monsters_tree, monster)
                
                # Restore custom prices
                self.custom_item_prices = settings.get('custom_prices', {})
                self.update_custom_prices_tree()
        except FileNotFoundError:
            pass

    def add_hover_effect(self, treeview):
        def on_enter(event):
            # Get the item (row) under the mouse cursor
            item = treeview.identify_row(event.y)
            
            # Remove hover tag from all items
            for i in treeview.get_children():
                treeview.item(i, tags=())
                
            # Add hover tag only to the item under cursor
            if item:
                treeview.item(item, tags=('hover',))
        
        def on_leave(event):
            # Remove hover tag from all items when mouse leaves treeview
            for item in treeview.get_children():
                treeview.item(item, tags=())
        
        # Configure the hover style
        style = ttk.Style()
        style.configure("Treeview", 
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b"
        )
        
        # Configure the hover tag
        treeview.tag_configure('hover', background='#353535')
        
        # Bind mouse events
        treeview.bind('<Motion>', on_enter)
        treeview.bind('<Leave>', on_leave)

    def edit_excluded_item(self, event):
        tree = event.widget
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        
        if not item:
            return
            
        # Get current value
        current_value = tree.item(item)['values'][0]
        
        # Create entry widget with consistent dark theme styling
        entry = ttk.Entry(tree, justify='center')
        entry.configure(foreground='black', background='#404040')
        entry.insert(0, current_value)
        
        # Position entry widget
        bbox = tree.bbox(item, '#1')  # Use '#1' instead of '#0'
        if not bbox:
            return
        x, y, w, h = bbox
        entry.place(x=x, y=y, width=w, height=h)
        
        entry.select_range(0, tk.END)
        entry.focus()
        
        def save_entry(event=None):
            new_value = entry.get().strip().lower()
            if new_value:
                tree.set(item, '#1', new_value)
                self.save_settings()
                self.reprocess_log_file()
                self.update_stats()
                self.calculate_totals()
            entry.destroy()
        
        entry.bind('<Return>', save_entry)
        entry.bind('<FocusOut>', save_entry)
        entry.bind('<Escape>', save_entry)

    def edit_custom_price_entry(self, event):
        tree = self.custom_prices_tree
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        
        if not item:
            return
            
        # Get current values
        current_values = tree.item(item)['values']
        
        # Edit item name
        if column == '#1':
            entry = ttk.Entry(tree, justify='center')
            entry.configure(foreground='black', background='#404040')
            entry.insert(0, current_values[0])
        # Edit price
        elif column == '#2':
            entry = ttk.Entry(tree, justify='center')
            entry.configure(foreground='black', background='#404040')
            entry.insert(0, str(current_values[1]).replace(',', ''))
            vcmd = (self.register(self.validate_price_input), '%P')
            entry.configure(validate='key', validatecommand=vcmd)
        else:
            return
            
        # Position entry widget
        x, y, w, h = tree.bbox(item, column)
        entry.place(x=x, y=y, width=w, height=h)
        entry.select_range(0, tk.END)
        entry.focus()
        
        def save_edit(event=None):
            if column == '#1':
                new_name = entry.get().strip().lower()
                if new_name:
                    old_name = current_values[0]
                    price = self.custom_item_prices[old_name]
                    del self.custom_item_prices[old_name]
                    self.custom_item_prices[new_name] = price
            else:
                try:
                    new_price = int(entry.get())
                    self.custom_item_prices[current_values[0]] = new_price
                except ValueError:
                    entry.destroy()
                    return
                    
            self.update_custom_prices_tree()
            self.save_settings()
            entry.destroy()
        
        entry.bind('<Return>', save_edit)
        entry.bind('<FocusOut>', save_edit)
        entry.bind('<Escape>', save_edit)

    def setup_about_tab(self):
        about_frame = ttk.Frame(self.notebook)
        self.notebook.add(about_frame, text="About")
        
        # Center container
        center_frame = ttk.Frame(about_frame)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Load and create round image
        image = PhotoImage(file=self.resource_path('profile.png'))
        image_label = ttk.Label(center_frame, image=image)
        image_label.image = image
        image_label.pack(pady=(0, 20))
        
        # Developer label
        dev_label = ttk.Label(center_frame, 
                            text="Developed by @yun.m",
                            style='Medium.TLabel')
        dev_label.pack(pady=(0, 20))
        
        # Version with larger font
        version_label = ttk.Label(center_frame,
                                text="Version 1.0.0",
                                font=('TkDefaultFont', 16, 'bold'))
        version_label.pack(pady=(0, 20))
        
        # Discord button
        discord_button = ttk.Button(center_frame,
                                text="DM me on Discord",
                                style='Rounded.TButton',
                                command=self.open_discord)
        discord_button.pack(pady=(0, 20))

    def open_discord(self):
        import webbrowser
        webbrowser.open('https://discordapp.com/users/148334042100531200')
        
    def resource_path(self, relative_path):
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            # If not running as bundled exe, use the current directory
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = MediviaAnalyzer()
    app.mainloop()
