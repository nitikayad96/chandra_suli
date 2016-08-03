"""
Check for unique lists within an array
"""

def unique_list(array, elements_to_check=0):
    """

    :param array: Array of lists to be checked
    :param elements_to_check: range of numbers corresponding to indices of list
    :return: new unique array
    """

    n_rows = len(array)

    unique_array = []

    if elements_to_check == 0:

        elements = range(len(array[0]))

    else:

        elements = elements_to_check


# for each row

    for i in range(n_rows):

        row_a = array[i]

        equal_row = False

        # for all subsequent rows

        for j in range(i+1,n_rows):

            row_b = array[j]

            # check if each element in rows are equal, breaking after finding even one unequal element

            for k in elements:

                equal_element = True

                if row_a[k] != row_b[k]:

                    equal_element = False
                    break

            if equal_element == True:

                equal_row = True
                break

        if equal_row == True:

            pass

        # append all unique rows to new array

        else:

            unique_array.append(row_a)


    return unique_array














