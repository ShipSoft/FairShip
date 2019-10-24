#include "fairlogger/Logger.h"

namespace ship {

template <fair::Severity severity, class T>
void log(T arg)
{
   for (bool fairLOggerunLikelyvariable = false; fair::Logger::Logging(severity) && !fairLOggerunLikelyvariable;
        fairLOggerunLikelyvariable = true)
      fair::Logger(severity, __FILE__, CONVERTTOSTRING(__LINE__), __FUNCTION__).Log() << arg;
}

template <fair::Severity severity, class T, class... Types>
void log(T arg, Types... args)
{
   log<severity>(arg);
   log<severity>(args...);
}

template <class T>
void log(T arg)
{
   constexpr fair::Severity severity = fair::Severity::INFO;
   for (bool fairLOggerunLikelyvariable = false; fair::Logger::Logging(severity) && !fairLOggerunLikelyvariable;
        fairLOggerunLikelyvariable = true)
      fair::Logger(severity, __FILE__, CONVERTTOSTRING(__LINE__), __FUNCTION__).Log() << arg;
}

template <class... Types>
void warn(Types &&... args)
{
   log<fair::Severity::warning>(std::forward<Types>(args)...);
}

template <class... Types>
void debug(Types &&... args)
{
   log<fair::Severity::debug>(std::forward<Types>(args)...);
}

template <class... Types>
void fatal(Types &&... args)
{
   log<fair::Severity::fatal>(std::forward<Types>(args)...);
}

template <class... Types>
void log(Types &&... args)
{
   log<fair::Severity::info>(std::forward<Types>(args)...);
}

} // namespace ship
