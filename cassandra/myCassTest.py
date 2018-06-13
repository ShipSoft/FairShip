from cassandra.cluster import Cluster
cluster = Cluster(protocol_version=3)
session = cluster.connect()
session.set_keyspace('test')
#session.execute("CREATE TYPE address (street text, zipcode int)")
#session.execute("CREATE TABLE jobs (j_id int PRIMARY KEY, company varchar, position varchar, location address)")

# create a class to map to the "address" UDT
# class Address(object):

#    def __init__(self, street, zipcode):
#        self.street = street
#        self.zipcode = zipcode

#cluster.register_user_type('test', 'address', Address)

# insert a row using an instance of Address
# session.execute("INSERT INTO jobs (j_id, company, position, location) VALUES (%s, %s, %s, %s)",
#               (0, 'KPMG', 'Developer', Address("123 Main St.", 78723)))

# results will include Address instances
results = session.execute("SELECT * FROM users")

row = results[0]
print row.u_id, row.first_name, row.last_name

print "=================-- ALL THE RECORDS --=================";

rows = results
for row in rows:
    print row.u_id, row.first_name, row.last_name
    

# Create a username with password
# CREATE USER 'username' WITH PASSWORD 'password' SUPERUSER;

# Assign permissions to a user based on the keyspace
# GRANT ALL ON KEYSPACE 'keyspace_name' TO 'username';


