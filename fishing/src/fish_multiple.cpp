#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cstdlib>
#include <tuple>
#include <random>

namespace py = pybind11;

enum catches {
    SHARK = 5,
    LARGE_FISH = 25,
    MEDIUM_FISH = 50,
    SMALL_FISH = 80,
    TRASH = 100
};

enum catches_bait {
    SHARK_BAIT = 35,
    LARGE_FISH_BAIT = 65,
    MEDIUM_FISH_BAIT = 80,
    SMALL_FISH_BAIT = 90,
    TRASH_BAIT = 100
};

enum fish_rarity {
    LEGENDARY = 10,
    SHINY = 40,
    NORMAL = 100
};

enum catch_rarity {
    VERY_COMMON = 1,
    COMMON = 2,
    UNCOMMON = 3,
    RARE = 4,
    ULTRA_RARE = 5
};

struct Grab_sharks {
    std::string shark_name;
    std::string shark_rarity;
    int coins_gained;
};

struct Grab_fish {
    std::string fish_rarity;
    std::string fish_size;
    int coins_gained;
};

int coins_to_give_for_sharks(std::string shark_rarity, catch_rarity catch_rarity, int boost_amount = 1) {
    if (shark_rarity == "normal") {
        switch (catch_rarity) {
            case catch_rarity::VERY_COMMON:
                return 10 * boost_amount;
            case catch_rarity::COMMON:
                return 15 * boost_amount;
            case catch_rarity::UNCOMMON:
                return 20 * boost_amount;
            case catch_rarity::RARE:
                return 25 * boost_amount;
            case catch_rarity::ULTRA_RARE:
                return 30 * boost_amount;
        }
    }
    else if (shark_rarity == "shiny") {
        switch (catch_rarity) {
            case catch_rarity::VERY_COMMON:
                return 20 * boost_amount;
            case catch_rarity::COMMON:
                return 25 * boost_amount;
            case catch_rarity::UNCOMMON:
                return 30 * boost_amount;
            case catch_rarity::RARE:
                return 35 * boost_amount;
            case catch_rarity::ULTRA_RARE:
                return 40 * boost_amount;
        }
    }
    else if (shark_rarity == "legendary") {
        switch (catch_rarity) {
            case catch_rarity::VERY_COMMON:
                return 30 * boost_amount;
            case catch_rarity::COMMON:
                return 35 * boost_amount;
            case catch_rarity::UNCOMMON:
                return 40 * boost_amount;
            case catch_rarity::RARE:
                return 45 * boost_amount;
            case catch_rarity::ULTRA_RARE:
                return 50 * boost_amount;
        }
    }
}

int coins_to_give_for_fish(catches size, std::string fish_rarity,  int boost_amount = 1) {
    if (fish_rarity == "trash") {
        return 1 * boost_amount;
    } else if (fish_rarity == "normal") {
        switch(size) {
            case catches::LARGE_FISH:
                return 6 * boost_amount;
            case catches::MEDIUM_FISH:
                return 4 * boost_amount;
            case catches::SMALL_FISH:
                return 2 * boost_amount;
        }
    } else if (fish_rarity == "shiny") {
        switch(size) {
            case catches::LARGE_FISH:
                return 9 * boost_amount;
            case catches::MEDIUM_FISH:
                return 7 * boost_amount;
            case catches::SMALL_FISH:
                return 5 * boost_amount;
        }
    } else if (fish_rarity == "legendary") {
        switch(size) {
            case catches::LARGE_FISH:
                return 14 * boost_amount;
            case catches::MEDIUM_FISH:
                return 12 * boost_amount;
            case catches::SMALL_FISH:
                return 10 * boost_amount;
        }
    }
}

Grab_sharks grab_shark_fishing_no_bait(std::vector<std::string> shark_names, int boost_amount = 1) {
    
    std::random_device rd;
    std::mt19937 gen(rd()); //mersenee twister engine
    std::uniform_int_distribution<int> dist(0, shark_names.size() - 1);
    
    int rand_idx = dist(gen);

    std::string shark_caught = shark_names[rand_idx];
    std::string rarity = "normal";
    int coins_gained = coins_to_give_for_sharks(rarity, catch_rarity::COMMON, boost_amount);
    return {shark_caught, rarity, coins_gained};
}

Grab_fish grab_fish(catches Fish_rarity, int boost_amount = 1) {
    std::random_device rd;
    std::mt19937 gen(rd()); //mersenee twister engine
    std::uniform_int_distribution<int> dist(0, 100);
    
    int rarity = dist(gen);
    std::string fish_rarity;
    std::string fish_size;
    int coins_gotten;

    switch(Fish_rarity) {
        case catches::LARGE_FISH:
            fish_size = "large";
            break;
        case catches::MEDIUM_FISH:
            fish_size = "medium";
            break;
        case catches::SMALL_FISH:
            fish_size = "small";
            break;
    }

    if (rarity <= fish_rarity::LEGENDARY) {
        fish_rarity = "legendary";
    } else if (rarity <= fish_rarity::SHINY) {
        fish_rarity = "shiny";
    } else if (rarity <= fish_rarity::NORMAL) {
        fish_rarity = "normal";
    }

    coins_gotten = coins_to_give_for_fish(Fish_rarity, fish_rarity, boost_amount);
    return {fish_rarity, fish_size, coins_gotten};
}

struct final_return {
    std::vector<std::tuple<std::string, std::string>> sharks_caught; // shark rarity, shark name
    std::vector<std::tuple<std::string, int>> large_fish_caught; // rarity, count 
    std::vector<std::tuple<std::string, int>> medium_fish_caught;
    std::vector<std::tuple<std::string, int>> small_fish_caught;
    int coins_gotten;
};

final_return fish(int how_many_times, std::string net, bool boost, int fish_odds, std::vector<std::string> shark_names, int boost_amount = 1, bool bait = false) {

    std::vector<std::tuple<std::string, std::string>> sharks_caught; // shark rarity, shark name
    std::vector<std::tuple<std::string, int>> large_fish_caught;  // rarity, count 
    std::vector<std::tuple<std::string, int>> medium_fish_caught; // rarity, count
    std::vector<std::tuple<std::string, int>> small_fish_caught;  // rarity, count
    int coins_gotten = 0;

    if (!boost) {
        boost_amount = 1;
    }

    for (int i = 0; i <= how_many_times; i++){
        if (!bait) {
            int rand_int = rand() % 101; // random number between 0 and 100
            if (rand_int <= fish_odds) { // did it catch anything?
                int catch_type = rand() % 101;
                if (catch_type <= catches::SHARK) {
                    Grab_sharks result = grab_shark_fishing_no_bait(shark_names, boost_amount);
                    sharks_caught.push_back(std::make_tuple(result.shark_rarity, result.shark_name));
                    coins_gotten += result.coins_gained;
                } else if (catch_type <= catches::LARGE_FISH) {
                    Grab_fish result = grab_fish(catches::LARGE_FISH, boost_amount);
                    int count = 1;
                    bool found = false;
                    for (auto &fish_type : large_fish_caught) {
                        if (std::get<0>(fish_type) == result.fish_rarity) {
                            count = std::get<1>(fish_type);
                            count++;
                            std::get<1>(fish_type) = count;
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        large_fish_caught.push_back(std::make_tuple(result.fish_rarity, count));
                    }
                    coins_gotten += result.coins_gained;
                } else if (catch_type <= catches::MEDIUM_FISH) {
                    Grab_fish result = grab_fish(catches::MEDIUM_FISH, boost_amount);
                    int count = 1;
                    bool found = false;
                    for (auto &fish_type : medium_fish_caught) {
                        if (std::get<0>(fish_type) == result.fish_rarity) {
                            count = std::get<1>(fish_type);
                            count++;
                            std::get<1>(fish_type) = count;
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        medium_fish_caught.push_back(std::make_tuple(result.fish_rarity, count));
                    }
                    coins_gotten += result.coins_gained;
                } else if (catch_type <= catches::SMALL_FISH) {
                    Grab_fish result = grab_fish(catches::SMALL_FISH, boost_amount);
                    int count = 1;
                    bool found = false;
                    for (auto &fish_type : small_fish_caught) {
                        if (std::get<0>(fish_type) == result.fish_rarity) {
                            count = std::get<1>(fish_type);
                            count++;
                            std::get<1>(fish_type) = count;
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        small_fish_caught.push_back(std::make_tuple(result.fish_rarity, count));
                    }
                    coins_gotten += result.coins_gained;
                } else if (catch_type <= catches::TRASH) {
                    coins_gotten = coins_to_give_for_fish(catches::TRASH, "not really needed.", boost_amount);
                }
            }
        } else {
            int rand_int = rand() % 101; // random number between 0 and 100
            if (rand_int <= fish_odds) { // did it catch anything?
                int catch_type = rand() % 101;
                if (catch_type <= catches_bait::SHARK_BAIT) {
                    Grab_sharks result = grab_shark_fishing_no_bait(shark_names, boost_amount);
                    sharks_caught.push_back(std::make_tuple(result.shark_rarity, result.shark_name));
                    coins_gotten += result.coins_gained;
                } else if (catch_type <= catches_bait::LARGE_FISH_BAIT) {
                    Grab_fish result = grab_fish(catches::LARGE_FISH, boost_amount);
                    int count = 1;
                    bool found = false;
                    for (auto &fish_type : large_fish_caught) {
                        if (std::get<0>(fish_type) == result.fish_rarity) {
                            count = std::get<1>(fish_type);
                            count++;
                            std::get<1>(fish_type) = count;
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        large_fish_caught.push_back(std::make_tuple(result.fish_rarity, count));
                    }
                    coins_gotten += result.coins_gained;

                } else if (catch_type <= catches_bait::MEDIUM_FISH_BAIT) {
                    Grab_fish result = grab_fish(catches::MEDIUM_FISH, boost_amount);
                    int count = 1;
                    bool found = false;
                    for (auto &fish_type : medium_fish_caught) {
                        if (std::get<0>(fish_type) == result.fish_rarity) {
                            count = std::get<1>(fish_type);
                            count++;
                            std::get<1>(fish_type) = count;
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        medium_fish_caught.push_back(std::make_tuple(result.fish_rarity, count));
                    }
                    coins_gotten += result.coins_gained;
                } else if (catch_type <= catches_bait::SMALL_FISH_BAIT) {
                    Grab_fish result = grab_fish(catches::SMALL_FISH, boost_amount);
                    int count = 1;
                    bool found = false;
                    for (auto &fish_type : small_fish_caught) {
                        if (std::get<0>(fish_type) == result.fish_rarity) {
                            count = std::get<1>(fish_type);
                            count++;
                            std::get<1>(fish_type) = count;
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        small_fish_caught.push_back(std::make_tuple(result.fish_rarity, count));
                    }
                    coins_gotten += result.coins_gained;
                } else if (catch_type <= catches_bait::TRASH_BAIT) {
                    coins_gotten = coins_to_give_for_fish(catches::TRASH, "not really needed.", boost_amount);
                }
            }
        }
    }
    return {sharks_caught, large_fish_caught, medium_fish_caught, small_fish_caught, coins_gotten};
}

PYBIND11_MODULE(fish_multiple, m) {
    // return struct
    py::class_<final_return>(m, "FinalReturn")
        .def_readonly("sharks_caught", &final_return::sharks_caught) // Interpreted by python as list[tuple[str, str]]
        .def_readonly("large_fish_caught", &final_return::large_fish_caught) // Interpreted by python as list[tuple[str, int]]
        .def_readonly("medium_fish_caught", &final_return::medium_fish_caught) // Interpreted by python as list[tuple[str, int]]
        .def_readonly("small_fish_caught", &final_return::small_fish_caught) // Interpreted by python as list[tuple[str, int]]
        .def_readonly("coins_gotten", &final_return::coins_gotten); // Interpreted by python as int
    
    // fish function
    m.def("fish_multiple_times", &fish,
        py::arg("times"), // argument/parameter
        py::arg("net"),
        py::arg("boost"),
        py::arg("fish_odds"),
        py::arg("shark_names"),
        py::arg("boost_amount") = 1,
        py::arg("bait") = false
    );
}