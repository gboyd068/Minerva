import json

settings_json = json.dumps([{ "type": "title", "title": "Settings" },
                            
                            { "type": "bool",
                            "title": "Setting 1",
                            "desc": "Description of setting 1",
                            "section": "General",
                            "key": "boolexample" },

                            { "type": "path",
                            "title": "Library Path",
                            "desc": "",
                            "section": "General",
                             "key": "pathexample" },
                             
                             { "type": "options",
                              "title": "Options",
                              "desc": "Option description",
                              "section": "General",
                              "key": "optionexample",
                              "options": ["option1", "option2", "option3"]},
                              ])