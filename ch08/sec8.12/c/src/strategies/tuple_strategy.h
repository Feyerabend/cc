#ifndef TUPLE_STRATEGY_H
#define TUPLE_STRATEGY_H

#include "../core/property_test.h"

Strategy* tuple2_strategy_create(Strategy* first_strategy, Strategy* second_strategy);

Strategy* tuple3_strategy_create(
    Strategy* first_strategy,
    Strategy* second_strategy,
    Strategy* third_strategy
);

#endif
