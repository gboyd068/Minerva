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

                            { "type": "bool",
                            "title": "Setting 1",
                            "desc": "Description of setting 1",
                            "section": "General",
                            "key": "boolexample" },

                            

                            { "type": "title", "title": "Audio" },

                            # playback speed

                            # skip distance

                            { "type": "title", "title": "Text" },

                            # font size

                            # margins

                            # line spacing?

                            # font


                              ])