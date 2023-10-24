import json

settings_json = json.dumps([{ "type": "title", "title": "General" },
                            
                            # library path
                            { "type": "path",
                            "title": "Library Path",
                            "desc": "",
                            "section": "General",
                            "key": "library_path" },

                            # app theme
                            { "type": "options",
                            "title": "Theme",
                            "desc": "",
                            "section": "General",
                            "key": "theme",
                            "options": ["Light", "Dark"]},

                            # { "type": "bool",
                            # "title": "Setting 1",
                            # "desc": "Description of setting 1",
                            # "section": "General",
                            # "key": "boolexample" },

                            

                            { "type": "title", "title": "Audio" },

                            # playback speed HMMMMMMMMM

                            # skip distance
                            { "type": "numeric",
                            "title": "Skip Distance",
                            "desc": "Time Skipped by Skip Buttons (seconds)",
                            "section": "General",
                            "key": "skip_size" },

                            { "type": "title", "title": "Text" },

                            # font size
                            { "type": "numeric",
                            "title": "Font Size",
                            "desc": "Ebook font size",
                            "section": "General",
                            "key": "font_size" },

                            # margins
                            { "type": "numeric",
                            "title": "Text Margin",
                            "desc": "Sets the page margins",
                            "section": "General",
                            "key": "textmargin" },

                            # line spacing?

                            # font


                              ])