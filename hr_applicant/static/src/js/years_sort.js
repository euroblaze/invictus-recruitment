function customSorter(a, b)
{
                    if (a) {
                        year_a = parseInt(a.split(" ")[0])
                        mont_a = parseInt(a.split(" ")[2])
                        year_b = parseInt(b.split(" ")[0])
                        mont_b = parseInt(b.split(" ")[2])
                        if ((year_a > year_b)) return 1;
                        if ((year_b > year_a)) return -1;
                        if ((year_a === year_b) & (mont_a > mont_b)) return 1;
                        if ((year_a === year_b) & (mont_b > mont_a)) return -1;}
                    return 0;
}