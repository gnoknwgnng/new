#include<stdio.h>
#include<stdlib.h>
void TOH(int , char, char, char);
void main()
{
	int n;
	printf("enter no of dics");
	scanf("%d",&n);
	if(n<0)
	printf("enter valid dics");
	else
	TOH(n,'A','B','C');
}
void TOH(int n,char a,char b,char c)
{
	if(n>0)
	{
		TOH(n-1,a,c,b);
		printf("%d is moved from %c to %c\n",n,a,c);
		TOH(n-1,b,a,c);
	}
}
