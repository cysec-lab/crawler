

def main():
    result_dir = 'D:/修士/研究/data/result/13'

    with open(result_dir + '/achievement/and_diff_of_word_in_new_page.csv', 'r') as f:
        content = f.read()

    a = 0

    lines = content.split('\n')
    for line in lines:
        if not line:
            break
        if line.startswith('URL'):
            continue
        value = line.split(',')
        if int(value[-2]) < 5:
            if int(value[-3]) > 0:
                print(value[1:], value[0])
                a += 1
    print(a)

if __name__ == '__main__':
    main()
