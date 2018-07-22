"""
This file will try to help us understand the calculations we need to make for
our coda operations management page.

We'll start the calculation by assuming that we already know the Unique Unit Name
and the Comprising Item name.

We'll then list all the things we already know about our Item.
These things include:
    - Items per Unit
    - Units Needed
    - Units Complete
    - Disassemble Requested
    - Disassemble Complete
    - Items in Stock
    - Items on Order

We'll then try to use that information to find out these things:
    - Items Needed
    - Items to Order

Prior to all this, we'll need to figure out the Items in Stock, this is the
only prior that can not be easily looked up from user input, so we need to
calculate it from those other priors

The Items in Stock caclulation will have these things as prior knowledge:
    - Items Recieved
    - Items in Return Process
    - Items Returned
    - Items per Unit
    - Units Complete
    - Disassemble Complete

These two calculations both rely on underlying data, and in the case of calculating
Items to Order we need to already know Items in Stock. However, this is the only
place where the two tables touch one another; in all other calculations the
tables are only to reference the most primitive prior available.

The difference between Catalog and In Stock is that Catalog contains all the
items that we currently have in our possession. On the other hand, In Stock
contains only the things that we have available for use (some sort of Action).
I.e. we can build unit with items we have In Stock, but not necessarily with
items we have in Catalog.

P: If item is in stock
Q: Item can be used
P -> Q

P: If item is in stock
Q: Item is in Catalog
P -> Q

In neither case is the converse a true statement for all items.

I'm not committed to the names In Stock and Catalog, in fact in the Coda doc
we are using Catalog and Inventory. It seems like there is a potential additional
category that just contains everything we have ever purchased ever, regardless
of if we have returned it. That might also be a useful tool, and that seems closer
to the idea of a Catalog. So, I'm not sure how to go about naming these things,
I'll just wait until I have a chance to talk to Jess about it.

In terms of organization, eventually we'd like to be able to add additional
attributes to the system. For example, we'd like to be able to deploy devices to
customers. This requires being able to calculate how the number of units deployed
relates to the number of Units in stock, this means there's an additional level
of abstraction that has to sit on top of this, so figuring out reliable
interfaces and naming conventions is really important

I propose an "Action" "Action Complete" paradigm. Because while "Order" "Recieved"
could also work, not all words have a corrolarry. Furthermore, while "Disassemble"
has the complete version of "Disassembled", the word "Ordered" does not at all
mean that the action of getting an item has been completed. I wish there were a
word that meant "to wish for or request" and "to have recieved or been granted".
It would implicitly state that if the thing hasn't been finished it will keep
going until it is. This way you could say something is some superposition of
being done or on the way to being inevitably done.
I would make the word 'carg' and the past tense 'carged'.

I carg hamburgers. I carged hamburgers.

It would be perfect.

Put simply, the code does this:
Given:
                recieved    : the number of this item recieved
                returns     : "   "      "  "    "    returns started
        returns_complete    : "   "      "  "    "    completely returned
                on_order    : "   "      "  "    "    on order
                per_unit    : "   "      "  "    "    per unit
                complete    : the number of units complete
    disassemble_complete    : "   "      "  "     completely disassembled
                needed   : "   "      "  "     that use this item needed to be built

*Note

owned = recieved - returns_complete
in_stock = owned - (complete * per_unit) + (disassemble_complete * per_unit) - (returns - returns_complete)
needed = (units_needed * per_unit)
deficit = needed - in_stock
to_order = deficit - on_order

In full, the equation for to_order is:
(needed * per_unit) - recieved - returns_complete - (complete * per_unit) + (disassemble_complete * per_unit) - on_order - (returns - returns_complete)
or reduced
per_unit * (needed - complete + disassemble_complete) - recieved - on_order - returns


In Coda, the stages of the calculation look like this:
owned = recieved - returns_complete
items_in_units = per_unit * (complete - disassemble_complete)
in_stock = owned - (returns - returns_complete) - items_in_units
needed = (units_needed * per_unit)
deficit = needed - in_stock
to_order = deficit - on_order


Ok, done. Now, how should deployments work?
Deployment section
Location
Number Deployed
Date deployed
Work backwards - deploy 5 units
Customer
lot
geolocation
name

The math is basically the same for units as it is for items:
No it's not, I suck at estimating complixity, forgot that it's bidirectional:

owned = built - disassemble_complete

deploy_needed = deploy_ordered - deploy_complete
disassemble_needed = disassemble_ordered - disassemble_complete

in_stock = owned - deploy_complete + retrieve_complete

deficit = deploy_needed + disassemble_needed - in_stock
units_to_build = deficit - build_order

NOTE: In the above equation I don't represent the true nature of built and build_on_order
Here I show them as if built were all the complete units, and build_on_order were
ones that hadn't been completed
It reality, build_order is the superset of built, meaning that all built items
are build_order and built refers to
the number of those that are done being built
This means in Coda the real units_to_build formula is:
units_to_build = deficit - build_order - built


A couple quick notes:
It seems that this whole thing could be abstracted in two ways.
1.
Entry
Additions
Subtractions
Exit

That pattern can then be modularly repeated, where the exit of one set is the
entry to the next one.

E.g.
given units, find the number to build
Add:
things that increase the need to build
Remove:
the inverse of those things
Set the value of To Build

That seems like the kind of thing that could be better automated/understood
through that lens

2.
Categorization of items by actions, where all actions are allowed, but not all
are advisable (or would work in reality); latter category gives you errors


Dropdown for Customers

Unique id for unit data table listings
NO
Should units have a specific name
Can we generate a number as we create them?

Ok begin the code:
"""

def carg_owned(recieved, returns_complete):
    """ items that we have in our possession """
    return recieved - returns_complete

def carg_in_stock(owned, complete, disassemble_complete, per_unit, returns, returns_complete):
    """ items that we have available to use in units """
    return owned - (complete * per_unit) + (disassemble_complete * per_unit) - (returns - returns_complete)

def carg_needed(needed, per_unit):
    """ items needed for to complete our builds """
    return (needed * per_unit)

def carg_deficit(needed, in_stock):
    """ items that we need but don't already have in stock """
    return needed - in_stock

def carg_to_order(deficit, on_order):
    """ items that need to be ordered """
    return deficit - on_order

def calc_in_stock(recieved, returns_complete, complete, disassemble_complete, per_unit, returns):
    """ this function calculates the number of items that we have in stock """
    owned = carg_owned(recieved, returns_complete)
    return carg_in_stock(owned, complete, disassemble_complete, per_unit, returns, returns_complete)

def calc_deficit(needed, per_unit, recieved, returns_complete, complete, disassemble_complete, returns):
    """ this function calculates the number of items that we need to complete our build requests """
    in_stock = calc_in_stock(recieved, returns_complete, complete, disassemble_complete, per_unit, returns)
    needed = carg_needed(needed, per_unit)
    return carg_deficit(needed, in_stock)

def calc_to_order(needed, per_unit, recieved, returns_complete, complete, disassemble_complete, on_order, returns):
    """ this function calculates the number of items that we have yet to order to complete our build requests """
    deficit = calc_deficit(needed, per_unit, recieved, returns_complete, complete, disassemble_complete, returns)
    return carg_to_order(deficit, on_order)

def carg_units_owned(units_built, disassemble_complete):
    return units_built - disassemble_complete

def carg_deploy_needed(deploy_ordered, deploy_complete):
    return deploy_ordered - deploy_complete

def carg_disassemble_needed(disassemble_ordered, disassemble_complete):
    return disassemble_ordered - disassemble_complete

def carg_units_in_stock(units_owned, deploy_complete, retrieve_complete):
    return units_owned - deploy_complete + retrieve_complete

def carg_unit_deficit(deploy_needed, disassemble_needed, units_in_stock):
    return deploy_needed + disassemble_needed - units_in_stock

def carg_unit_to_build(unit_deficit, build_on_order):
    return unit_deficit - build_on_order

def calc_units_in_stock(units_built, disassemble_complete, deploy_complete, retrieve_complete):
    units_owned = carg_units_owned(units_built, disassemble_complete)
    return carg_units_in_stock(units_owned, deploy_complete, retrieve_complete)

def calc_unit_deficit(units_built, disassemble_complete, deploy_complete, retrieve_complete, deploy_needed, disassemble_needed):
    units_in_stock = calc_units_in_stock(units_built, disassemble_complete, deploy_complete, retrieve_complete)
    return carg_unit_deficit(deploy_needed, disassemble_needed, units_in_stock)

def calc_units_to_build(units_built, disassemble_complete, deploy_complete, retrieve_complete, deploy_needed, disassemble_needed, build_on_order):
    units_in_stock = calc_units_in_stock(units_built, disassemble_complete, deploy_complete, retrieve_complete)
    unit_deficit = calc_unit_deficit(units_built, disassemble_complete, deploy_complete, retrieve_complete, deploy_needed, disassemble_needed)
    return carg_unit_to_build(unit_deficit, build_on_order)

# These are the tests that can be run with the command pytest
def test_standard():
    """
    this is a standard test
    with these inputs we should expect to have:
    9 items in stock
    6 additional items needed
    4 remaining to order
    """
    recieved = 25
    returns = 4
    returns_complete = returns
    per_unit = 3
    complete = 5
    disassemble_complete = 1
    needed = 5
    on_order = 2

    assert 9 == calc_in_stock(recieved, returns_complete, complete, disassemble_complete, per_unit, returns)

    assert 6 == calc_deficit(needed, per_unit, recieved, returns_complete, complete, disassemble_complete, returns)

    assert 4 == calc_to_order(needed, per_unit, recieved, returns_complete, complete, disassemble_complete, on_order, returns)

def test_too_few_recieved():
    """
    this is a test of having too few recieved items (negative in_stock)
    with these inputs we should expect to have:
    9 items in stock
    6 additional items needed
    4 remaining to order
    """
    recieved = 6
    returns = 4
    returns_complete = returns
    per_unit = 3
    complete = 5
    disassemble_complete = 1
    needed = 5
    on_order = 2

    assert -10 == calc_in_stock(recieved, returns_complete, complete, disassemble_complete, per_unit, returns)

    assert 25 == calc_deficit(needed, per_unit, recieved, returns_complete, complete, disassemble_complete, returns)

    assert 23 == calc_to_order(needed, per_unit, recieved, returns_complete, complete, disassemble_complete, on_order, returns)

def test_too_many_in_stock():
    """
    this is a test of having too few recieved items (negative in_stock)
    with these inputs we should expect to have:
    9 items in stock
    6 additional items needed
    4 remaining to order
    """
    recieved = 60
    returns = 4
    returns_complete = returns
    per_unit = 3
    complete = 5
    disassemble_complete = 1
    needed = 5
    on_order = 2

    assert 44 == calc_in_stock(recieved, returns_complete, complete, disassemble_complete, per_unit, returns)

    assert -29 == calc_deficit(needed, per_unit, recieved, returns_complete, complete, disassemble_complete, returns)

    assert -31 == calc_to_order(needed, per_unit, recieved, returns_complete, complete, disassemble_complete, on_order, returns)

def test_incomplete_returns():
    """
    this is a test of having incomplete returns
    with these inputs we should expect to have:
    9 items in stock
    6 additional items needed
    4 remaining to order
    """
    recieved = 15
    returns = 5
    returns_complete = 3
    # 10 in stock, 12 owned
    per_unit = 2
    complete = 5
    disassemble_complete = 1
    # 8 items used
    # 2 items left in stock
    needed = 2
    # deficit of 2 items
    on_order = 1
    # need to order 1 item

    assert 2 == calc_in_stock(recieved, returns_complete, complete, disassemble_complete, per_unit, returns)

    assert 2 == calc_deficit(needed, per_unit, recieved, returns_complete, complete, disassemble_complete, returns)

    assert 1 == calc_to_order(needed, per_unit, recieved, returns_complete, complete, disassemble_complete, on_order, returns)

def test_deploy():
    """
    An example of a deployment
    """
    units_built = 6
    disassemble_complete = 2
    # only 4 owned here
    deploy_ordered = 4
    deploy_complete = 1
    deploy_needed = deploy_ordered - deploy_complete
    # deploy_needed is 3
    disassemble_ordered = 3
    disassemble_needed = disassemble_ordered - disassemble_complete
    # disassemble_needed is 1
    retrieve_complete = 1
    # in stock is 4
    # deficit is 0
    build_on_order = 1
    # to build is -1

    assert 4 == calc_units_in_stock(units_built, disassemble_complete, deploy_complete, retrieve_complete)

    assert 0 == calc_unit_deficit(units_built, disassemble_complete, deploy_complete, retrieve_complete, deploy_needed, disassemble_needed)

    assert -1 == calc_units_to_build(units_built, disassemble_complete, deploy_complete, retrieve_complete, deploy_needed, disassemble_needed, build_on_order)

def test_deploy_2():
    """
    An example of a deployment
    """
    units_built = 10
    disassemble_complete = 3
    # 7 owned
    deploy_ordered = 5
    deploy_complete = 4
    deploy_needed = deploy_ordered - deploy_complete
    # deploy needed is 1
    disassemble_ordered = 5
    disassemble_needed = disassemble_ordered - disassemble_complete
    # disassemble_needed = 2
    retrieve_complete = 2
    # in stock is 5
    # deficit -2
    build_on_order = 2
    # to build is -4

    assert 5 == calc_units_in_stock(units_built, disassemble_complete, deploy_complete, retrieve_complete)

    assert -2 == calc_unit_deficit(units_built, disassemble_complete, deploy_complete, retrieve_complete, deploy_needed, disassemble_needed)

    assert -4 == calc_units_to_build(units_built, disassemble_complete, deploy_complete, retrieve_complete, deploy_needed, disassemble_needed, build_on_order)

def test_deploy_3():
    """
    An example of a deployment
    """
    units_built = 3
    disassemble_complete = 2
    # 1 owned
    deploy_ordered = 7
    deploy_complete = 2
    deploy_needed = deploy_ordered - deploy_complete
    # deploy needed is 5
    disassemble_ordered = 3
    disassemble_needed = disassemble_ordered - disassemble_complete
    # disassemble_needed = 1
    retrieve_complete = 1
    # in stock is 0
    # deficit 4
    build_on_order = 2
    # to build is 2

    assert 0 == calc_units_in_stock(units_built, disassemble_complete, deploy_complete, retrieve_complete)

    assert 6 == calc_unit_deficit(units_built, disassemble_complete, deploy_complete, retrieve_complete, deploy_needed, disassemble_needed)

    assert 4 == calc_units_to_build(units_built, disassemble_complete, deploy_complete, retrieve_complete, deploy_needed, disassemble_needed, build_on_order)
