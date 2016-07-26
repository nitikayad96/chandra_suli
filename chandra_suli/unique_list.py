"""
Check for unique lists within an array
"""

def unique_list(array):

    n_rows = len(array)
    n_elements = len(array[0])

    unique_array = []

# for each row

    for i in range(n_rows):

        row_a = array[i]

        equal_row = False

        # for all subsequent rows

        for j in range(i+1,n_rows):

            row_b = array[j]

            # check if each element in rows are equal, breaking after finding even one unequal element

            for k in range(n_elements):

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














