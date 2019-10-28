#pragma once
#include "FairLogger.h"

namespace ship {

namespace details {

template <fair::Severity severity, class T>
void log(fair::Logger& logger, T arg)
{
    if (fair::Logger::Logging(severity)) {
        logger << arg;
    }
}

template <fair::Severity severity, class T, class... Types>
void log(fair::Logger& logger, T arg, Types... args)
{
    log<severity>(logger, arg);
    log<severity>(logger, args...);
}

}

template <fair::Severity severity, class... Types>
void log(Types... args)
{
    fair::Logger logger(severity, __FILE__, to_string(__LINE__), __FUNCTION__);
    details::log<severity>(logger.Log(), args...);
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
