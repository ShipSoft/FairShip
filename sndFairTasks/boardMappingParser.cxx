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


tuple<map<string, map<string, map<string, int>> >, map<string, map<string, map<string, string>> > > oldMapping(string path)
{
  // station mapping for SciFi
  map<string, map<int, int> > stations { {"M1Y", {{0,29}, {1,3},  {2,30}}},
                                       // three fibre mats per plane
                                       {"M1X", {{0,11}, {1,17}, {2,28}}},
                                       {"M2Y", {{0,16}, {1,14}, {2,18}}},
                                       {"M2X", {{0,1},  {1,2},  {2,25}}},
                                       {"M3Y", {{0,15}, {1,9},  {2,5}}},
                                       {"M3X", {{0,22}, {1,27}, {2,4}}},
                                       {"M4Y", {{0,46}, {1,23}, {2,20}}},
                                       {"M4X", {{0,8},  {1,50}, {2,49}}},
                                       {"M5Y", {{0,19}, {1,13}, {2,36}}},
                                       {"M5X", {{0,21}, {1,10}, {2,6}}} };
  if ( path.find("commissioning-h6") != string::npos )
  {
       stations["M4Y"] = {{0,46}, {1,40}, {2,20}}; // board 40 replaces 23       
  }
  
  // Board Maps for Scifi
  string board{};
  for (auto plane : stations)
  {
    for (auto mat : stations[plane.first])
    {
      board = Form("board_%i", mat.second);
      boardMaps["Scifi"][board][plane.first] = mat.first;      
    }
  }
  
  // Board Maps for MuFilter
  // hopefully final mapping of TI18
  boardMapsMu["MuFilter"]["board_52"] = { {"B", "Veto_1Left"}, {"C", "Veto_1Right"}, 
                                          {"A", "Veto_2Left"}, {"D", "Veto_2Right"} };
  boardMapsMu["MuFilter"]["board_43"] = { {"D", "US_1Left"}, {"A", "US_1Right"},
                                          {"C", "US_2Left"}, {"B", "US_2Right"} };
  boardMapsMu["MuFilter"]["board_60"] = { {"D", "US_3Left"}, {"A", "US_3Right"},
                                          {"C", "US_4Left"}, {"B", "US_4Right"} };
  boardMapsMu["MuFilter"]["board_41"] = { {"D", "US_5Left"}, {"A", "US_5Right"},
                                          {"C", "DS_1Left"}, {"B", "DS_1Right"} };
  boardMapsMu["MuFilter"]["board_42"] = { {"D", "DS_2Left"}, {"A", "DS_2Right"},
                                          {"B", "DS_1Vert"}, {"C", "DS_2Vert"} };
  boardMapsMu["MuFilter"]["board_55"] = { {"D", "DS_3Left"}, {"A", "DS_3Right"},
                                          {"B", "DS_3Vert"}, {"C", "DS_4Vert"} };
  
  // string.find func: If no matches are found, the function returns string::npos.
  if (path.find("commissioning-h6") != string::npos || path.find("TB_data_commissioning") != string::npos)
  {
    // H6 / H8  
    boardMapsMu["MuFilter"]["board_43"] = { {"A", "US_1Left"}, {"B", "US_2Left"},
                                            {"C","US_2Right"}, {"D", "US_1Right"} };
    boardMapsMu["MuFilter"]["board_60"] = { {"A","US_3Left"},  {"B","US_4Left"},
                                            {"C","US_4Right"}, {"D","US_3Right"} };
    boardMapsMu["MuFilter"]["board_41"] = { {"A","US_5Left"},  {"B","DS_1Left"},
                                            {"C","DS_1Right"}, {"D","US_5Right"} };
    if (path.find("commissioning-h6") != string::npos)
    {
      boardMapsMu["MuFilter"]["board_59"] = { {"A","DS_2Right"},  {"B","DS_2Vert"},
                                            {"C","DS_1Vert"},  {"D","DS_2Left"} };
    }
    else
    {
      boardMapsMu["MuFilter"]["board_59"] = { {"A","DS_2Left"},  {"B","DS_1Vert"},
                                            {"C","DS_2Vert"},  {"D","DS_2Right"} };
    }
    boardMapsMu["MuFilter"]["board_42"] = { {"A","DS_3Left"},  {"B","DS_4Vert"},
                                            {"C","DS_3Vert"},  {"D","DS_3Right"} };
    boardMapsMu["MuFilter"]["board_52"] = { {"A","Veto_2Left"},  {"B","Veto_1Left"},
                                            {"C","Veto_1Right"}, {"D","Veto_2Right"} };
  }
  if (path.find("data_commissioning_dune") != string::npos)  // does not work
  {
    boardMapsMu["MuFilter"]["board_43"] = { {"A", "US_1Left"}, {"B", "US_2Left"},
                                          {"C", "US_2Right"}, {"D", "US_1Right"} };
    boardMapsMu["MuFilter"]["board_60"] = { {"A", "US_3Left"}, {"B", "US_4Left"},
                                          {"C", "US_4Right"}, {"D", "US_3Right"} };
    boardMapsMu["MuFilter"]["board_41"] = { {"A", "US_5Left"}, {"B", "DS_1Left"},
                                          {"C", "DS_1Right"}, {"D", "US_5Right"} };
    boardMapsMu["MuFilter"]["board_59"] = { {"A", "DS_2Left"}, {"B", "DS_1Vert"},
                                          {"C", "DS_2Vert"}, {"D", "DS_2Right"} };
    boardMapsMu["MuFilter"]["board_42"] = { {"A", "DS_3Left"}, {"B", "DS_3Vert"},
                                          {"C", "notconnected"}, {"D", "notconnected"} };
    boardMapsMu["MuFilter"]["board_52"] = { {"A", "DS_3Right"}, {"B", "notconnected"},
                                          {"C", "notconnected"}, {"D", "notconnected"} };
  }
  return make_tuple(boardMaps, boardMapsMu);
}

/* The next lines are used for tests. 
void main()
{
  TString server = gSystem->Getenv("EOSSHIP");
  // path used for code functionality tests
  string path    = "/eos/experiment/sndlhc/testbeam/commissioning-h6/run_000010/";
    
 // Read json file into a string
 std::ifstream jsonfile(Form("%s/%s/board_mapping.json", server.Data(), path.c_str()));
 json j;
 jsonfile >> j;

 getBoardMapping(j);
 //oldMapping(path);
}
*/
