namespace ReaSynthetic;

public static class Fixture
{
    public static int Add(int left, int right) => left + right;

#if SECOND_METHOD
    public static int Multiply(int left, int right) => left * right;
#endif
}
