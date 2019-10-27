#include "FairLogger.h"
#pragma once

namespace ship {

template <fair::Severity severity, class T>
void log(T arg)
{
    if (fair::Logger::Logging(severity)) {
        fair::Logger(severity, __FILE__, to_string(__LINE__), __FUNCTION__).Log() << arg;
    }
}

template <fair::Severity severity, class T, class... Types>
void log(T arg, Types... args)
{
    log<severity>(arg);
    log<severity>(args...);
}

template <class... Types>
void fatal(Types... args)
{
    log<fair::Severity::fatal>(args...);
}

template <class... Types>
void error(Types... args)
{
    log<fair::Severity::error>(args...);
}

template <class... Types>
void warn(Types... args)
{
    log<fair::Severity::warning>(args...);
}

template <class... Types>
void info(Types... args)
{
    log<fair::Severity::info>(args...);
}

template <class... Types>
void debug(Types... args)
{
    log<fair::Severity::debug>(args...);
}

} // namespace ship
