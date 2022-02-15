// This is the C++ version of shipLHC/rawData/boardMappingParser.py
#include <iostream>
#include <sstream>
#include <fstream>
#include <string>
#include <map>
#include <tuple>
#include "nlohmann/json.hpp"
#include "TString.h" // to use Form

using namespace std;
using json = nlohmann::json;

map<string, map<string, map<string, int>> > boardMaps{};
map<string, map<string, map<string, string>> > boardMapsMu{};

using json = nlohmann::json;

namespace quicktype {
  struct Info
  {
    string Class;
    string type;
    int board;
    vector<string> slots;
  };
  struct Info_scifi
  {
    string Class;
    string type;
    vector<int> boards;
  };
    
  inline json get_untyped(const json &j, const char *property) {
        if (j.find(property) != j.end()) {
            return j.at(property).get<json>();
        }
        return json();
    }
}

namespace nlohmann {

    inline void from_json(const json& _j, struct quicktype::Info& _x) {
        _x.Class = _j.at("class").get<string>();
        _x.type  = _j.at("type").get<string>();
        _x.board = _j.at("board").get<int>();
        _x.slots = _j.at("slots").get<vector<string>>();
    }

    inline void to_json(json& _j, const struct quicktype::Info& _x) {
        _j = json{{"class", _x.Class}, {"type", _x.type}, {"board", _x.board}, {"slots", _x.slots}};
    }
    inline void from_json(const json& _j, struct quicktype::Info_scifi& _x) {
        _x.Class = _j.at("class").get<string>();
        _x.type  = _j.at("type").get<string>();
        _x.boards = _j.at("boards").get<vector<int>>();
    }

    inline void to_json(json& _j, const struct quicktype::Info_scifi& _x) {
        _j = json{{"class", _x.Class}, {"type", _x.type}, {"boards", _x.boards}};
    }
}

tuple<map<string, map<string, map<string, int>> >, map<string, map<string, map<string, string>> > > getBoardMapping(json j)
{
   /* 
   the mapping is structured as: {<subsystem>: {<plane>: {<settings>...}, ...}, ...}
   subsystem is veto, scifi, us, ds
   plane depends on subsystem (e.g. '1x', '1y'... for Scifi)
   settings depends on sybsystem as well
   more info here: https://gitlab.cern.ch/snd-scifi/software/-/wikis/Board-Mapping
   */
  
  // Seperate structure for scifi than other subsystems 
  quicktype::Info info;
  quicktype::Info_scifi info_scifi;
  
  string bString;
  char c;
    
  for (auto& el : j.items())
   {
    // Loop over the planes in the subsystem
    for (auto& subel : el.value().items())
    {
      string jsonStr = subel.value().dump();
            
      // Each subsystem is treated separately
      if (el.key() =="scifi")
      {
        info_scifi = nlohmann::json::parse(jsonStr);
        // sanity check that the settings are correct
        if (info_scifi.Class != "multiboard" || info_scifi.type != "snd_scifi")
        {
          cout << "Wrong class/type: " << info_scifi.Class << "/" << info_scifi.type << endl;
          break;
        }
        // Loop over the boards (for SciFi)
        for (int i = 0; i < info_scifi.boards.size(); i++)
        {
          bString = Form("board_%i", info_scifi.boards.at(i));
          c =::toupper(subel.key()[1]);
          boardMaps["Scifi"][bString][Form("M%c%c", subel.key()[0], c )] = i;          
        }
      }
      else if (el.key() =="veto")
      {
        info = nlohmann::json::parse(jsonStr);
        // sanity check that the settings are correct
        if (info.Class != "multislot" || info.type != "snd_veto")
        {
          cout << "Wrong class/type: " << info.Class << "/" << info.type << endl;
          break;
        }
        // Add the "board_XX' entry in the dictionary if not already there
        bString = Form("board_%i", info.board);
        if (boardMapsMu["MuFilter"].find(bString.c_str()) == boardMapsMu["MuFilter"].end())
        {
          boardMapsMu["MuFilter"][bString] = {};
        }          
        // Loop over the slots (the first is always left, the second always right)
        for (int i = 0; i < info.slots.size(); i++)
        {
          bString = Form("board_%i", info.board);
          if (i==0) boardMapsMu["MuFilter"][bString][info.slots.at(i)] = Form("Veto_%dLeft", stoi(subel.key()));
          else if (i==1) boardMapsMu["MuFilter"][bString][info.slots.at(i)] = Form("Veto_%dRight", stoi(subel.key()));
        }
      }
      else if (el.key() =="us")
      {
        info = nlohmann::json::parse(jsonStr);
        // sanity check that the settings are correct
        if (info.Class != "multislot" || info.type != "snd_us")
        {
          cout << "Wrong class/type: " << info.Class << "/" << info.type << endl;
          break;
        }
        // Add the "board_XX' entry in the dictionary if not already there
        bString = Form("board_%i", info.board);
        if (boardMapsMu["MuFilter"].find(bString.c_str()) == boardMapsMu["MuFilter"].end())
        {
          boardMapsMu["MuFilter"][bString] = {};
        }
        // Loop over the slots (the first is always left, the second always right)
        for (int i = 0; i < info.slots.size(); i++)
        {
          bString = Form("board_%i", info.board);
          if (i==0) boardMapsMu["MuFilter"][bString][info.slots.at(i)] = Form("US_%iLeft", stoi(subel.key()));
          else if (i==1) boardMapsMu["MuFilter"][bString][info.slots.at(i)] = Form("US_%iRight", stoi(subel.key()));
        }
      }
      else if (el.key() =="ds")
      {
        info = nlohmann::json::parse(jsonStr);
        // sanity check that the settings are correct
        if (info.Class != "multislot" || (info.type != "snd_dsh" && info.type != "snd_dsv"))
        {
          cout << "Wrong class/type: " << info.Class << "/" << info.type << endl;
          break;
        }
        // Add the "board_XX' entry in the dictionary if not already there
        bString = Form("board_%i", info.board);
        if (boardMapsMu["MuFilter"].find(bString.c_str()) == boardMapsMu["MuFilter"].end())
        {
          boardMapsMu["MuFilter"][bString] = {};
        }
        // for DS we have the additional complication of vertival planes, 
        // but they are two different plane types (snd_dsh and snd_dsv)
        if(info.type == "snd_dsh")
        {
          // Loop over the slots (the first is always left, the second always right)
          for (int i = 0; i < info.slots.size(); i++)
          {
            bString = Form("board_%i", info.board);
            if (i==0) boardMapsMu["MuFilter"][bString][info.slots.at(i)] = Form("DS_%iLeft", stoi(subel.key()));
            else if (i==1) boardMapsMu["MuFilter"][bString][info.slots.at(i)] = Form("DS_%iRight", stoi(subel.key()));
          }
        }
        else
        {
          boardMapsMu["MuFilter"][bString][info.slots.at(0)] = Form("DS_%iVert", stoi(subel.key()));
        }
      }
      else 
      {
        cout << "Unknown subsystem " << el.key() <<endl;
        break;
      }
    }
   }
   return make_tuple(boardMaps, boardMapsMu);
}
