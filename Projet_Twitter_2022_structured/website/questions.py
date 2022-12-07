from . import dictFollowed, dictFollowing, dictUIDToUser, dictUsernameToUID

def get_symetric_relationship():
    #Question 1.a
    #Creating follow_relationship list (since maintaining it every time someone follows someone else would be too costly and we never call this function)
    follow_relationship = []
    for uid in dictFollowing:
        for uid2 in dictFollowing[uid]:
            follow_relationship.append((uid, uid2))
    #Actual algorithm
    symetric_relations = set()
    temp = set()
    for uid, uid2 in follow_relationship:
        if uid < uid2:
            if temp.__contains__((uid, uid2)):
                symetric_relations.add((uid, uid2))
            else:
                temp.add((uid, uid2))
        else:
            if temp.__contains__((uid2, uid)):
                symetric_relations.add((uid2, uid))
            else:
                temp.add((uid2, uid))
    return symetric_relations

def get_symetric_relationship2():
    #Question 1.a but without creating follow_relationship (which is less efficient)
    symetric_relations = set()
    for uid in dictFollowing:
        for uid2 in dictFollowing[uid]:
            if uid in dictFollowing[uid2]:
                symetric_relations.add((uid, uid2))
    return symetric_relations

def get_username_of_symetric_relationship():
    #Question 1.b (by reverting dictUsernameToUID)
    usernames = set()
    dict_uid_to_name = {v:k for k, v in dictUsernameToUID.items()}
    symetric_relations = get_symetric_relationship()
    for uid, uid2 in symetric_relations:
        usernames.add(dict_uid_to_name[uid])
        usernames.add(dict_uid_to_name[uid2])
    return usernames

def get_username_of_symetric_relationship():
    #Question 1.b (with our data structure)
    usernames = set()
    symetric_relations = get_symetric_relationship2()
    for uid, uid2 in symetric_relations:
        usernames.add(dictUIDToUser[uid].username)
        usernames.add(dictUIDToUser[uid2].username)
    return usernames

def get_followers_of_followers(user):
    # Question 2
    #We could also use a hahsmap user.id : followers of followers to get that list in O(1) but we thought this would be efficient enough (this is O(n) and n is the size of the output)
    fof = set()
    for uid1 in dictFollowed[user.id]:
        for uid2 in dictFollowed[uid1]:
            fof.add(dictUIDToUser[uid2])
    return fof