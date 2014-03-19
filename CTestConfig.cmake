# Dashboard is opened for submissions for a 24 hour period starting at
# the specified NIGHLY_START_TIME. Time is specified in 24 hour format.
set(CTEST_PROJECT_NAME "PandaRoot")
set(CTEST_NIGHTLY_START_TIME "00:00:00 CEST")

set(CTEST_DROP_METHOD "http")
set(CTEST_DROP_SITE "cdash.gsi.de")
set(CTEST_DROP_LOCATION "/CDash/submit.php?project=PandaRoot")
set(CTEST_DROP_SITE_CDASH TRUE)
#set(CTEST_TRIGGER_SITE "")

set(CTEST_TESTING_TIMEOUT 300)
