// This is the C++ version of shipLHC/rawData/boardMappingParser.py
#ifndef BOARDMAP_H
#define BOARDMAP_H 1

#include <iostream>
#include <string>
#include <map>
#include <tuple>
#include "nlohmann/json.hpp"

using namespace std;
using json = nlohmann::json;

tuple<map<string, map<string, map<string, int>> >, map<string, map<string, map<string, string>> > > getBoardMapping(json j);
tuple<map<string, map<string, map<string, int>> >, map<string, map<string, map<string, string>> > > oldMapping(string path);

#endif
